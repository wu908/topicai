/**
 * 项目屏工作区：左对话（项目助手）+ 右产物 + 确认卡。
 * 对齐原型结构；数据走 /api/v2（对话 ask、确认卡 HumanGate/action）。
 */
import { useCallback, useMemo, useState } from 'react';
import { Box, Typography } from '@mui/material';
import ProjectChat, { type ChatMessage } from './ProjectChat';
import ArtifactPane from './ArtifactPane';
import type { ConfirmCardProps } from './ConfirmCard';
import {
  decideHumanGate,
  respondToAction,
} from '@/services/api/v2/projects';
import type { CalibrationWorkspace } from '@/types/contracts/v2/content';
import { extractErrorMessage } from '@/utils/error';
import { askCompanion } from '@/services/api/v2/companion';

function makeKey(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function WorkspaceAiDock(props: {
  workspace: CalibrationWorkspace | null;
  busy?: boolean;
  onChanged?: () => void;
  onSend?: (text: string) => void;
  onBodyChange?: (v: string) => void;
  onConfirmCandidate?: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const action = props.workspace?.orchestrated_action;
  const project = props.workspace?.project;
  const version = props.workspace?.current_version ?? null;

  const push = (msg: ChatMessage) => setMessages((m) => [...m, msg]);

  const handleSend = (text: string) => {
    push({ id: makeKey('me'), role: 'me', text });
    const context = [
      project?.title ? `标题：${project.title}` : '',
      project?.content_form ? `形态：${project.content_form}` : '',
      '身份：项目助手，只处理这一条内容。',
      '规则：不替用户拍板；建议要短；改正文请用户在编辑器操作。',
    ]
      .filter(Boolean)
      .join('\n');
    void askCompanion({ context, question: text })
      .then((res) => {
        const answer =
          res?.data?.answer?.trim() ||
          '模型暂时没有给出答复。你可以在右侧改稿，或稍后再问我。';
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
    props.onSend?.(text);
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
        text: '已按你的确认推进。可以继续改稿或做下一步。',
        source: '已写入审计记录',
      });
      props.onChanged?.();
    } catch (e) {
      setErr(extractErrorMessage(e, '确认失败，请重试'));
      // ConfirmCard 需要感知失败，不能把"同意"当成已写入。
      throw e;
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
          text: '已否决并记录原因。流程不会卡住：可以改稿，或稍后在「今日」继续。',
          source: '已写入审计记录',
        });
        props.onChanged?.();
      } catch (e) {
        setErr(extractErrorMessage(e, '否决失败，请重试'));
        throw e;
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
      busy: busy || props.busy,
      onAgree: accept,
      onReject: reject,
      afterReject: [
        { label: '改稿', onPick: () => undefined },
        { label: '暂时搁置', onPick: () => undefined },
      ],
    };
    if (action.human_gate_type === 'intent' || action.action_type === 'confirm_intent') {
      return { ...base, type: 'intent', title: '这条内容想让读者产生什么变化？' };
    }
    if (action.human_gate_type === 'content_version' || action.action_type === 'review_candidate') {
      return {
        ...base,
        type: 'fact',
        title: '请确认：这段内容是否表达了你想说的意思？',
      };
    }
    if (
      action.human_gate_type === 'publication' ||
      action.action_type === 'confirm_publish_scope' ||
      action.action_type === 'record_publication'
    ) {
      return { ...base, type: 'publish', title: '发布前请确认' };
    }
    return { ...base, type: 'public_scope' };
  }, [action, accept, busy, props.busy, reject]);

  return (
    <Box sx={{ mb: 2 }}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1.2fr 340px' },
          gap: 1.25,
          minHeight: 520,
          height: 'min(75vh, 760px)',
        }}
      >
        <ProjectChat
          messages={messages}
          confirmCard={confirmCard}
          busy={busy}
          onSend={handleSend}
          projectName={project?.title}
        />
        <ArtifactPane
          title={version?.title || project?.title || ''}
          body={version?.body_text || ''}
          onBodyChange={props.onBodyChange}
          onConfirmCandidate={props.onConfirmCandidate}
          workspace={props.workspace}
        />
      </Box>
      {err ? (
        <Typography role="alert" variant="caption" sx={{ color: 'error.main', display: 'block', mt: 1 }}>
          {err}
        </Typography>
      ) : null}
    </Box>
  );
}
