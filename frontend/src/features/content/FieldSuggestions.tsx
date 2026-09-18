import { useCallback, useEffect, useRef, useState } from 'react';
import { AutoAwesomeOutlined, RefreshOutlined } from '@mui/icons-material';
import { suggestFieldCandidates } from '@/services/api/v2/projects';
import { extractErrorMessage } from '@/utils/error';
import type { FieldSuggestionCandidate, SuggestionField } from '@/types/contracts/v2/content';

interface FieldSuggestionsProps {
  projectId: string;
  field: SuggestionField;
  /** 正在回答的问题（answer 字段用它对准问题） */
  question?: string | null;
  /** 已经写下的内容：非空时按它改进，而不是另起一句 */
  currentText?: string;
  onPick: (text: string) => void;
  disabled?: boolean;
}

/**
 * 「AI 先给几个方向」：候选点一下填进输入框，文字仍然可以任意改写。
 *
 * 三条产品底线（用户明确要求过）：
 * 1. 候选不是选项墙——它是把"面对空输入框"换成"改一句话"，所以不做成 select；
 * 2. AI 不可用时也要有候选（后端给通用方向/写法骨架），并说明来源；
 * 3. 每次取候选都是一次真实调用，所以进来取一次、要换再点「换一批」。
 */
export default function FieldSuggestions({
  projectId,
  field,
  question = null,
  currentText = '',
  onPick,
  disabled = false,
}: FieldSuggestionsProps) {
  const [candidates, setCandidates] = useState<FieldSuggestionCandidate[]>([]);
  const [source, setSource] = useState<'ai' | 'deterministic_fallback' | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // StrictMode 会把挂载跑两遍：一次性布尔锁会被 cleanup 永久锁死（本轮踩过），
  // 所以用递增令牌，只有最后一次请求的结果才落地。
  const tokenRef = useRef(0);
  // 「已经取过哪一次」必须放 ref：放进 state 时第二次 effect 跑在 setState 生效
  // 之前，守卫看得见 null → 真实调用变成两次（测试里实测到 2 次）。
  const loadedKeyRef = useRef<string | null>(null);

  const load = useCallback(async () => {
    const token = tokenRef.current + 1;
    tokenRef.current = token;
    setLoading(true);
    setError(null);
    try {
      const result = await suggestFieldCandidates(projectId, {
        field,
        question: question ?? undefined,
        current_text: currentText || undefined,
        count: 3,
      });
      if (tokenRef.current !== token) return;
      setCandidates(result.candidates);
      setSource(result.source);
      setNote(result.limitations[0] ?? null);
    } catch (err) {
      if (tokenRef.current !== token) return;
      setCandidates([]);
      setSource(null);
      setNote(null);
      setError(extractErrorMessage(err, '这次没取到方向，稍后再试'));
    } finally {
      if (tokenRef.current === token) setLoading(false);
    }
  }, [projectId, field, question, currentText]);

  // 进入面板自动取一次：用户不该为了看到候选先点一个按钮。
  useEffect(() => {
    const key = `${projectId}:${field}`;
    if (loadedKeyRef.current === key) return;
    loadedKeyRef.current = key;
    void load();
  }, [load, projectId, field]);

  if (error) {
    return (
      <p className="field-suggestions-note">
        {error}
        <button type="button" className="field-suggestions-retry" disabled={disabled || loading} onClick={() => void load()}>
          重试
        </button>
      </p>
    );
  }

  if (loading && candidates.length === 0) {
    return <p className="field-suggestions-note">正在给几个方向…</p>;
  }

  if (candidates.length === 0) return null;

  return (
    <div className="field-suggestions" aria-label="AI 给的方向">
      <div className="field-suggestions-head">
        <span>
          <AutoAwesomeOutlined fontSize="inherit" />
          {source === 'ai' ? 'AI 给的方向' : '先给你几个方向'}
          （点一下填进去，可以随便改）
        </span>
        <button type="button" className="field-suggestions-refresh" disabled={disabled || loading} onClick={() => void load()}>
          <RefreshOutlined fontSize="inherit" />
          换一批
        </button>
      </div>
      <div className="field-suggestions-chips">
        {candidates.map((candidate) => (
          <button
            key={candidate.text}
            type="button"
            className="field-suggestion"
            disabled={disabled}
            title={candidate.why}
            onClick={() => onPick(candidate.text)}
          >
            {candidate.text}
            {candidate.why ? <small>{candidate.why}</small> : null}
          </button>
        ))}
      </div>
      {note ? <p className="field-suggestions-note">{note}</p> : null}
    </div>
  );
}
