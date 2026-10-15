/**
 * 全局 AI：灵感速记 + 全站操控入口（与项目助手分离）。
 * 名称/头像等设置只在侧栏「设置 · 全局 AI」里改，面板只读展示。
 */
import { useEffect, useState } from 'react';
import {
  loadIdentities,
  subscribeIdentities,
  type AiIdentity,
} from './aiIdentity';
import { askCompanion } from '@/services/api/v2/companion';
import { extractErrorMessage } from '@/utils/error';

/** 与 aiIdentity.toneStyles 同源的预览色 */
const toneStyles: Record<'a' | 'b' | 'c' | 'd', string> = {
  a: 'radial-gradient(circle at 30% 28%, #fff, rgba(143,190,232,.6))',
  b: 'radial-gradient(circle at 30% 28%, #fff, rgba(201,138,75,.55))',
  c: 'radial-gradient(circle at 30% 28%, #fff, rgba(25,30,38,.25))',
  d: 'radial-gradient(circle at 30% 28%, #fff, rgba(143,190,232,.25))',
};

function Avatar({ identity }: { identity: AiIdentity }) {
  const toneCss = identity.avatar
    ? undefined
    : toneStyles[identity.tone] ?? toneStyles.a;
  return (
    <div
      className="ai-avatar"
      aria-hidden
      style={
        identity.avatar
          ? { backgroundImage: `url(${identity.avatar})`, backgroundSize: 'cover' }
          : { background: toneCss }
      }
    >
      {identity.avatar ? '' : (identity.name || 'A').slice(0, 1)}
    </div>
  );
}

export default function GlobalAIPanel() {
  const [open, setOpen] = useState(false);
  const [identity, setIdentity] = useState<AiIdentity>(() => loadIdentities().global);
  const [draft, setDraft] = useState('');
  const [log, setLog] = useState<Array<{ role: 'me' | 'ai'; text: string }>>([]);
  const name = identity.name;

  // 设置页改名/换头像后面板同步
  useEffect(() => subscribeIdentities(() => setIdentity(loadIdentities().global)), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey && e.code === 'Space') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const send = () => {
    const v = draft.trim();
    if (!v) return;
    setLog((l) => [...l, { role: 'me', text: v }]);
    setDraft('');
    void askCompanion({
      context: [
        '身份：全局助手，用于灵感速记与全站操控说明。',
        '规则：先复述用户意思；不要代用户做发布/公开/长期经验/删除决定。',
        '可以说：建议先记进「想发的」，或立成一条内容。',
      ].join('\n'),
      question: v,
    })
      .then((res) => {
        const answer =
          res?.data?.answer?.trim() ||
          '暂时没有答复。你可以再说一句，或点侧栏「设置」检查模型接口。';
        setLog((l) => [...l, { role: 'ai', text: answer }]);
      })
      .catch((e) => {
        setLog((l) => [...l, { role: 'ai', text: extractErrorMessage(e, '连接模型失败，稍后重试') }]);
      });
  };

  return (
    <>
      <div className={`ai-panel${open ? ' open' : ''}`} role="dialog" aria-label="全局 AI 助手" aria-hidden={!open}>
        <div className="ai-panel-h">
          <Avatar identity={identity} />
          <div className="ai-name-wrap">
            {/* 名称/头像只在侧栏「设置」里改，面板只读展示 */}
            <div className="ai-name" aria-label="AI 名称">{name}</div>
            <div className="ai-sub">全局助手 · 全站可用 · 不替代项目里的助手</div>
          </div>
          <button type="button" className="ai-close" aria-label="关闭" onClick={() => setOpen(false)}>
            ×
          </button>
        </div>

        <div className="ai-body">
          {log.length === 0 ? (
            <div className="ai-empty">
              <b>我是全局助手</b>，两件事最常用：
              <br />
              ① <strong>灵感速记</strong>：想到什么直接说，我帮你收进「想发的」
              <br />
              ② <strong>全局操控</strong>：让我替你跳转、建条、推进、对账
              <br />
              <br />
              <span style={{ opacity: 0.85 }}>
                改某一条稿请去项目里找「项目助手」；
                <br />
                发布、公开范围、长期经验、删除仍由你拍板。
              </span>
            </div>
          ) : (
            log.map((m, i) => (
              <div key={i} className={`msg-row${m.role === 'me' ? ' me' : ''}`}>
                <div className={`msg-av ${m.role === 'me' ? 'me' : 'ai'}`} aria-hidden>
                  {m.role === 'me' ? '你' : (name || 'A').slice(0, 1)}
                </div>
                <div className="msg-col">
                  <div className="msg-body">{m.text}</div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="copy-note">说清楚要什么就行。我会先确认你的意思，再动手，不替你做决定。</div>

        {/* 头像/名称设置移到侧栏「设置 · 全局 AI」，面板内不再提供 */}
        <div className="ai-foot">
          <div className="ai-input-row">
            <input
              id="aiInput"
              placeholder="记一条灵感，或让我帮你操作（如：把番茄钟标为待对账）…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <button type="button" className="ai-send" aria-label="发送" onClick={send}>
              ↑
            </button>
          </div>
          <div className="ai-tools">
            <button type="button" className="ai-tool">
              ＋ 附件
            </button>
            <button
              type="button"
              className="ai-tool"
              onClick={() =>
                setLog((l) => [
                  ...l,
                  { role: 'ai', text: '语音录入在开发中。你现在可以打字记灵感，或说「立成一条内容」。' },
                ])
              }
            >
              语音
            </button>
            <span style={{ flex: 1 }} />
            <button type="button" className="ai-tool" id="aiEditName">
              改名字
            </button>
          </div>
        </div>
      </div>

      <button
        type="button"
        className={`ball${open ? ' open' : ''}`}
        title="打开全局 AI"
        aria-label="打开全局 AI"
        onClick={() => setOpen((v) => !v)}
      />
    </>
  );
}
