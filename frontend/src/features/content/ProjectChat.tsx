/**
 * 项目对话流（content-line-prototype.html · msg-row / msg-body）。
 * 结构：stages → chat → strip(确认卡) → compose。
 */
import { useEffect, useRef, useState, type ReactNode } from 'react';
import {
  avatarLetter,
  avatarStyle,
  loadIdentities,
  type AiIdentity,
} from '@/features/companion/aiIdentity';
import ConfirmCard, { type ConfirmCardProps } from './ConfirmCard';

export interface ChatMessage {
  id: string;
  role: 'assistant' | 'me';
  text: string;
  source?: string;
}

function Avatar(props: { id: AiIdentity; size?: number }) {
  const size = props.size ?? 32;
  return (
    <div
      className="msg-av ai"
      aria-hidden
      style={
        props.id.avatar
          ? {
              width: size,
              height: size,
              backgroundImage: `url(${props.id.avatar})`,
              backgroundSize: 'cover',
              color: '#191e26',
            }
          : {
              width: size,
              height: size,
              background: avatarStyle(props.id),
              color: '#191e26',
            }
      }
    >
      {props.id.avatar ? '' : avatarLetter(props.id)}
    </div>
  );
}

export default function ProjectChat(props: {
  messages: ChatMessage[];
  confirmCard?: ConfirmCardProps | null;
  busy?: boolean;
  onSend: (text: string) => void;
  projectName?: string;
  /** 原型 .stages：放在对话区顶部 */
  stages?: ReactNode;
}) {
  const [draft, setDraft] = useState('');
  const [id, setId] = useState<AiIdentity>(() => loadIdentities().project);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sync = () => setId(loadIdentities().project);
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  const send = () => {
    const v = draft.trim();
    if (!v) return;
    props.onSend(v);
    setDraft('');
    window.setTimeout(() => {
      scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' });
    }, 30);
  };

  return (
    <div className="pane chat-pane">
      <div className="top-light" aria-hidden="true" />

      {props.stages ? <div className="stages">{props.stages}</div> : null}

      <div className="chat" ref={scroller}>
        {props.messages.length === 0 ? (
          <div className="msg-row">
            <Avatar id={id} size={32} />
            <div className="msg-col">
              <div className="msg-name">{id.name || '项目助手'} · 项目助手</div>
              <div className="msg-body">
                只处理这一条内容。你可以说「这段再短一点」或「先确认候选」。
                {props.projectName ? (
                  <span className="msg-src">当前条目 · {props.projectName.slice(0, 16)}</span>
                ) : null}
              </div>
            </div>
          </div>
        ) : (
          props.messages.map((m) => {
            const isMe = m.role === 'me';
            return (
              <div key={m.id} className={`msg-row${isMe ? ' me' : ''}`}>
                {isMe ? (
                  <div className="msg-av me" aria-hidden>
                    你
                  </div>
                ) : (
                  <Avatar id={id} size={32} />
                )}
                <div className="msg-col">
                  {!isMe ? (
                    <div className="msg-name">{id.name || '项目助手'} · 项目助手</div>
                  ) : null}
                  <div className="msg-body">
                    <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
                    {m.source ? <span className="msg-src">{m.source}</span> : null}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 原型 .strip：确认卡固定在对话与输入之间 */}
      {props.confirmCard ? (
        <div className="strip">
          <ConfirmCard {...props.confirmCard} variant="strip" />
        </div>
      ) : null}

      <div className="compose">
        <input
          placeholder="说一句想法，或「这段再短一点」…"
          aria-label="对项目助手说话"
          value={draft}
          disabled={props.busy}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button type="button" className="send" aria-label="发送" disabled={props.busy} onClick={send}>
          ↑
        </button>
      </div>
    </div>
  );
}
