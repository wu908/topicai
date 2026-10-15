/**
 * 项目屏（对齐 content-line-prototype.html · 项目屏）
 * 左：应用导航（AppLayout）｜ 中：对话信息流 ｜ 右：过程·结果
 * 不再叠旧 workspace 侧栏/表单壳。
 */
import { useCallback, useMemo, useState } from 'react';
import ProjectChat, { type ChatMessage } from './ProjectChat';
import ArtifactPane from './ArtifactPane';
import type { ConfirmCardProps } from './ConfirmCard';
import {
  decideHumanGate,
  respondToAction,
  createContentVersion,
} from '@/services/api/v2/projects';
import type { CalibrationWorkspace, Material } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { askCompanion } from '@/services/api/v2/companion';
import StageMeter from './StageMeter';

function makeKey(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function ProjectStagePage(props: {
  workspace: CalibrationWorkspace | null;
  materials?: Material[];
  onChanged?: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [body, setBody] = useState('');

  const project = props.workspace?.project;
  const version = props.workspace?.current_version;
  const action = props.workspace?.orchestrated_action;

  const push = (msg: ChatMessage) => setMessages((m) => [...m, msg]);

  const handleSend = (text: string) => {
    push({ id: makeKey('me'), role: 'me', text });
    const context = [
      project?.title ? `标题：${project.title}` : '',
      project?.content_form ? `形态：${project.content_form}` : '',
      '身份：项目助手，只处理这一条内容。',
      '规则：不替用户拍板；建议要短；改正文请用户在右侧「稿」操作。',
    ]
      .filter(Boolean)
      .join('\n');
    void askCompanion({ context, question: text })
      .then((res) => {
        const answer = res?.data?.answer?.trim() || '模型暂时没有答复。你可以在右侧改稿，或稍后再问我。';
        push({
          id: makeKey('ai'),
          role: 'assistant',
          text: answer,
          source: '项目助手 · 模型答复',
        });
      })
      .catch((e) => {
        push({
          id: makeKey('ai'),
          role: 'assistant',
          text: extractErrorMessage(e, '问模型失败，请稍后重试。'),
          source: '未能连接模型',
        });
      });
  };

  const accept = useCallback(async () => {
    if (!action) return;
    setBusy(true);
    setErr(null);
    try {
      const gate = action.human_gate;
      if (gate && gate.status === 'pending') {
        await decideHumanGate(gate.id, {
          decision: 'confirm',
          expected_gate_version: gate.version,
          idempotency_key: makeKey('gate-ok'),
        });
      }
      await respondToAction(action.id, {
        decision: 'accept',
        expected_action_version: action.version,
        idempotency_key: makeKey('act-ok'),
      });
      push({
        id: makeKey('ai'),
        role: 'assistant',
        text: '已按你的确认推进。',
        source: '已写入审计记录',
      });
      props.onChanged?.();
    } catch (e) {
      setErr(extractErrorMessage(e, '确认失败，请重试'));
    } finally {
      setBusy(false);
    }
  }, [action, props]);

  const reject = useCallback(
    async (reason: string) => {
      if (!action) return;
      setBusy(true);
      setErr(null);
      try {
        const gate = action.human_gate;
        if (gate && gate.status === 'pending') {
          await decideHumanGate(gate.id, {
            decision: 'reject',
            decision_payload: { reason },
            expected_gate_version: gate.version,
            idempotency_key: makeKey('gate-no'),
          });
        }
        await respondToAction(action.id, {
          decision: 'reject',
          response_payload: { reason },
          expected_action_version: action.version,
          idempotency_key: makeKey('act-no'),
        });
        push({
          id: makeKey('ai'),
          role: 'assistant',
          text: '已否决。可以改稿，或稍后在「今日」继续。',
          source: '已写入审计记录',
        });
        props.onChanged?.();
      } catch (e) {
        setErr(extractErrorMessage(e, '否决失败，请重试'));
      } finally {
        setBusy(false);
      }
    },
    [action, props],
  );

  const confirmCard = useMemo<ConfirmCardProps | null>(() => {
    if (!action || action.status === 'cancelled' || action.status === 'completed') return null;
    const base = {
      title: action.title,
      suggestion: action.title,
      reason: action.reason,
      busy,
      onAgree: accept,
      onReject: reject,
      afterReject: [
        { label: '改稿', onPick: () => undefined },
        { label: '暂时搁置', onPick: () => undefined },
      ],
    };
    if (action.human_gate_type === 'intent' || action.action_type === 'confirm_intent') {
      return { ...base, type: 'intent' as const, title: '这条内容想让读者产生什么变化？' };
    }
    if (action.human_gate_type === 'content_version' || action.action_type === 'review_candidate') {
      return {
        ...base,
        type: 'fact' as const,
        title: '请确认：这段内容是否表达了你想说的意思？',
      };
    }
    if (
      action.human_gate_type === 'publication' ||
      action.action_type === 'confirm_publish_scope' ||
      action.action_type === 'record_publication'
    ) {
      return { ...base, type: 'publish' as const, title: '发布前请确认' };
    }
    return { ...base, type: 'public_scope' as const };
  }, [action, accept, busy, reject]);

  const saveDraft = async (text: string) => {
    setBody(text);
    if (!project?.id || !project.current_version_id) return;
    setBusy(true);
    try {
      await createContentVersion(project.id, {
        title: project.title || '草稿',
        body_text: text,
        expected_project_version: project.version,
        idempotency_key: makeKey('ver'),
      });
      push({
        id: makeKey('ai'),
        role: 'assistant',
        text: '稿已保存新版本。',
        source: '已写入版本',
      });
      props.onChanged?.();
    } catch (e) {
      setErr(extractErrorMessage(e, '保存失败，请重试'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="lumen-topbar" style={{ padding: '10px 24px 8px' }}>
        <div>
          <h1 style={{ fontSize: 18 }}>{project?.title || '未命名项目'}</h1>
          <p className="sub" style={{ margin: 0 }}>
            项目助手只处理这一条内容
          </p>
        </div>
        <button type="button" className="lumen-btn sm ghost" onClick={() => props.onChanged?.()}>
          刷新
        </button>
      </div>

      <div className="lumen-stage">
        <ProjectChat
          messages={messages}
          confirmCard={confirmCard}
          busy={busy}
          onSend={handleSend}
          projectName={project?.title}
          stages={project ? <StageMeter project={project} /> : null}
        />
        <ArtifactPane
          title={version?.title || project?.title || ''}
          body={body || version?.body_text || ''}
          onBodyChange={(t) => void saveDraft(t)}
          workspace={props.workspace}
          materials={props.materials}
        />
      </div>
      {err ? (
        <p role="alert" style={{ color: '#b4574e', fontSize: 12, marginTop: 8 }}>
          {err}
        </p>
      ) : null}
    </div>
  );
}
