/**
 * 轻创建：一句话 → 只记下来（灵感）或 立成内容（项目）。
 * 对齐交互地图 v1.1 修订 A：轻进重出。
 */
import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addInboxItem } from '@/services/api/v2/asyncLoop';
import { startProject } from '@/services/api/v2/projects';
import { extractErrorMessage } from '@/utils/error';

export default function QuickCreatePanel() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [busy, setBusy] = useState<'note' | 'project' | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const noteOnly = useCallback(async () => {
    const v = text.trim();
    if (!v || busy) return;
    setBusy('note');
    setError(null);
    try {
      await addInboxItem({
        kind: 'idea',
        content: v,
        consent: 'private',
        idempotency_key: `home-note-${Date.now()}`,
      });
      setText('');
      setNotice('已记进「想发的」。要不要立成一条内容，随时可以再说。');
    } catch (err) {
      setError(extractErrorMessage(err, '记下来失败，请重试'));
    } finally {
      setBusy(null);
    }
  }, [text, busy]);

  const makeProject = useCallback(async () => {
    const v = text.trim();
    if (!v || busy) return;
    setBusy('project');
    setError(null);
    try {
      const started = await startProject({
        raw_input: v,
        idempotency_key: `home-start-${Date.now()}`,
      });
      setText('');
      const id = started?.project_id;
      setNotice('已立成一条内容。');
      navigate(id ? `/content/${id}` : '/content');
    } catch (err) {
      setError(extractErrorMessage(err, '立成内容失败，请重试'));
    } finally {
      setBusy(null);
    }
  }, [text, busy, navigate]);

  return (
    <section className="acard glass" aria-label="快速开始" style={{ marginTop: 18 }}>
      <p className="kicker" style={{ marginTop: 0 }}>
        快速开始 · 先说一句
      </p>
      <p className="pg-sub" style={{ marginTop: 0, marginBottom: 12 }}>
        记一笔就够，或做成一条内容。只想记下来，不会催你写稿。
      </p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          className="lm-input"
          style={{ flex: 1, minWidth: 220, marginBottom: 0, borderRadius: 9999, height: 44 }}
          placeholder="想到什么？例如：番茄钟别在下班后补…"
          aria-label="一句话想法"
          value={text}
          disabled={!!busy}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              void makeProject();
            }
          }}
        />
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={!!busy || !text.trim()}
          onClick={() => void noteOnly()}
        >
          {busy === 'note' ? '记下中…' : '只记下来'}
        </button>
        <button
          type="button"
          className="btn btn-text"
          disabled={!!busy || !text.trim()}
          onClick={() => void makeProject()}
        >
          {busy === 'project' ? '创建中…' : '立成内容 →'}
        </button>
      </div>
      {notice ? (
        <p className="pg-sub" role="status" style={{ marginTop: 10 }}>
          {notice}{' '}
          <button type="button" className="btn-text" onClick={() => navigate('/content')}>
            去内容里看
          </button>
        </p>
      ) : null}
      {error ? (
        <p className="login-err" role="alert" style={{ marginTop: 10 }}>
          {error}
        </p>
      ) : null}
    </section>
  );
}
