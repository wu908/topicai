/**
 * CompanionDialog — 悬浮球对话系统（DESIGN.md v3 §6 定稿）。
 *
 * 结构三体分离：悬浮球（可拖拽、六层构造）→ π 形灯框（消息区，底部开放
 * 不闭合）→ 独立输入泡（与消息框分离）。首次打开播放四幕全息入场（GSAP
 * timeline：输入泡伸出 → 灯带上升 → 顶帽交会 → 成像），仅播放一次
 * （sessionStorage 持久化）；闲置 12s 渐隐 chrome 只留气泡与输入泡。
 *
 * 轴向契约：任何界面调用 `openWith(ctx)` 注入上下文（ctx 芯片 + 回答）。
 * 红线：对话只提供回答/提议/可逆操作提示；四个不可替代决策仍由调用方
 * 显式提交（本组件不代为确认）。
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import { Box } from '@mui/material';
import { gsap } from 'gsap';

const BOOT_KEY = 'topicai-companion-booted';
const ZEN_DELAY = 12_000;

export default function CompanionDialog() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const threadRef = useRef<HTMLDivElement | null>(null);

  const [open, setOpen] = useState(false);
  const [zen, setZen] = useState(false);
  const [context, setContext] = useState('全局');
  const [messages, setMessages] = useState<Array<{ me: boolean; text: string }>>([]);
  const [draft, setDraft] = useState('');

  const mounted = useRef(false);
  const zenTimer = useRef<number | null>(null);

  /* ---------- 四幕入场（仅首次）；非首次快速淡入 ---------- */
  useEffect(() => {
    if (!open || !mounted.current) return;
    mounted.current = false;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduced && !sessionStorage.getItem(BOOT_KEY)) {
      const root = rootRef.current;
      const frame = frameRef.current;
      if (!root || !frame) return;
      const input = root.querySelector('.companion-inputbubble');
      const strips = root.querySelectorAll<HTMLElement>('.companion-strip');
      const cap = root.querySelector<HTMLElement>('.companion-topcap');
      const head = root.querySelector('.companion-winhead');
      const thread = root.querySelector('.companion-thread');
      const sheet = root.querySelector('.companion-framebg');
      const side = input ? (input.getBoundingClientRect().left > window.innerWidth / 2 ? 'right center' : 'left center') : 'left center';
      gsap.set(input, { autoAlpha: 0, scaleX: 0.22, transformOrigin: side });
      gsap.set(strips, { scaleY: 0, transformOrigin: 'bottom' });
      gsap.set(cap, { scaleX: 0, transformOrigin: 'center' });
      gsap.set([head, thread, sheet], { autoAlpha: 0, y: 12 });
      const tl = gsap.timeline({
        defaults: { ease: 'power3.out' },
        onComplete: () => sessionStorage.setItem(BOOT_KEY, '1'),
      });
      tl.addLabel('extend')
        .to(input, { autoAlpha: 1, scaleX: 1, duration: 0.5, ease: 'back.out(1.4)' }, 'extend')
        .addLabel('rise', 'extend+=0.42')
        .to(strips, { scaleY: 1, duration: 0.62, ease: 'power3.inOut', stagger: 0.07 }, 'rise')
        .addLabel('close', 'rise+=0.40')
        .to(cap, { scaleX: 1, duration: 0.45, ease: 'power2.out' }, 'close')
        .addLabel('image', 'close+=0.15')
        .to([head, thread, sheet], { autoAlpha: 1, y: 0, duration: 0.5, stagger: 0.07 }, 'image');
    } else {
      sessionStorage.setItem(BOOT_KEY, '1');
    }
  }, [open]);

  /* ---------- 渐隐：闲置 12s 只留气泡与输入泡 ---------- */
  const resetZen = useCallback(() => {
    setZen(false);
    if (zenTimer.current) window.clearTimeout(zenTimer.current);
    zenTimer.current = window.setTimeout(() => {
      if (open) setZen(true);
    }, ZEN_DELAY);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const kick = window.setTimeout(resetZen, 0);
    const wake = () => resetZen();
    const root = rootRef.current;
    root?.addEventListener('pointermove', wake);
    root?.addEventListener('focusin', wake);
    return () => {
      root?.removeEventListener('pointermove', wake);
      root?.removeEventListener('focusin', wake);
      window.clearTimeout(kick);
      if (zenTimer.current) window.clearTimeout(zenTimer.current);
    };
  }, [open, resetZen]);

  /* ---------- 打开：接受全局 openCompanion 上下文注入 ---------- */
  useEffect(() => {
    const onOpen = (event: Event) => {
      const detail = (event as CustomEvent<{ context?: string }>).detail;
      const ctx = detail?.context || '全局';
      setContext(ctx);
      setZen(false);
      setOpen(true);
      resetZen();
    };
    window.addEventListener('topicai:companion-open', onOpen);
    return () => window.removeEventListener('topicai:companion-open', onOpen);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const push = (text: string, me: boolean) => {
    setMessages((prev) => [...prev, { me, text }]);
    requestAnimationFrame(() => {
      const t = threadRef.current;
      if (t) t.scrollTop = t.scrollHeight;
    });
  };

  const submit = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft('');
    push(text, true);
    window.setTimeout(() => {
      push(
        '收到。（演示回复）接入真实模型后这里由带出处的编排器作答：可执行改提醒、换口味、重新生成等可逆操作；拾取、发布与长期经验仍需你亲手确认。',
        false,
      );
    }, 600);
  };

  const close = () => {
    setOpen(false);
    setZen(false);
  };

  return createPortal(
    <Box ref={rootRef} aria-label="AI 对话" sx={{ position: 'fixed', zIndex: 1300, right: 44, bottom: 44, pointerEvents: 'none' }}>
      {/* 悬浮球（可拖拽） */}
      <Box
        aria-label="对话悬浮球"
        component="button"
        type="button"
        onClick={() => (open ? close() : setOpen(true))}
        sx={{
          position: 'relative',
          width: 80,
          height: 80,
          border: 'none',
          borderRadius: '50%',
          cursor: 'grab',
          pointerEvents: 'auto',
          background: 'radial-gradient(circle at 30% 22%, #FFFFFF 0%, #EDF2F9 46%, #C9D8EA 100%)',
          boxShadow: '0 16px 40px rgba(70,95,130,.30), inset 0 2px 5px rgba(255,255,255,.95), 0 0 30px rgba(143,190,232,.32)',
          '&:hover': { boxShadow: '0 20px 48px rgba(70,95,130,.36), inset 0 2px 5px rgba(255,255,255,.95), 0 0 46px rgba(143,190,232,.42)' },
          '&:active': { cursor: 'grabbing', transform: 'scale(.98)' },
        }}
      >
        <Box aria-hidden sx={{ position: 'absolute', inset: -8, borderRadius: '50%', border: '2px solid transparent', borderTopColor: 'rgba(255,255,255,.98)', borderRightColor: 'rgba(143,190,232,.7)', pointerEvents: 'none', animation: 'orbit-spin 5s linear infinite' }} />
        <Box aria-hidden sx={{ position: 'absolute', inset: -15, borderRadius: '50%', border: '1.5px solid transparent', borderTopColor: 'rgba(143,190,232,.5)', pointerEvents: 'none', animation: 'orbit-spin 9s linear infinite reverse' }} />
        <Box sx={{ fontSize: 19, fontWeight: 800, color: '#41546E', pointerEvents: 'none', animation: 'companion-breathe 5s ease-in-out infinite' }}>✦</Box>
      </Box>

      {open ? (
        <Box
          ref={frameRef}
          sx={{
            position: 'absolute',
            right: 92,
            bottom: 8,
            width: 400,
            pointerEvents: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {/* π 形灯框（底部开放不闭合）：玻璃底渐隐 + 左右/顶灯带 */}
          <Box sx={{ position: 'relative', borderRadius: '24px 24px 0 0', overflow: 'hidden', px: 3, pb: 3 }}>
            <Box className="companion-framebg" sx={{ position: 'absolute', inset: 0, background: 'rgba(255,255,255,.34)', backdropFilter: 'blur(30px) saturate(160%)', border: '1px solid rgba(255,255,255,.75)', borderBottom: 'none', borderRadius: '24px 24px 0 0', maskImage: 'linear-gradient(180deg,#000 70%,transparent 100%)', WebkitMaskImage: 'linear-gradient(180deg,#000 70%,transparent 100%)', opacity: zen ? 0.06 : 1, transition: 'opacity 1.2s ease' }} />
            {['left', 'right'].map((side) => (
              <Box key={side} className="companion-strip" sx={{ position: 'absolute', top: 12, bottom: 26, width: 2, [side]: 0, borderRadius: 2, overflow: 'hidden', background: 'rgba(255,255,255,.55)', opacity: zen ? 0.06 : 1, transition: 'opacity 1.2s ease' }}>
                <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '40%', background: 'linear-gradient(180deg,transparent,#FFFFFF 38%,#8FBEE8 72%,transparent)', animation: side === 'right' ? 'companion-flow 3s cubic-bezier(.45,.05,.35,1) 1.5s infinite' : 'companion-flow 3s cubic-bezier(.45,.05,.35,1) infinite' }} />
              </Box>
            ))}
            <Box className="companion-topcap" sx={{ position: 'absolute', top: 11, left: 12, right: 12, height: 2, borderRadius: 2, overflow: 'hidden', background: 'rgba(255,255,255,.55)', opacity: zen ? 0.06 : 1, transition: 'opacity 1.2s ease' }}>
              <Box sx={{ position: 'absolute', inset: 0, background: 'linear-gradient(90deg,transparent,#fff 45%,#8FBEE8 70%,transparent)', opacity: 0.6 }} />
            </Box>

            <Box className="companion-winhead" sx={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 10, pt: 3, pb: 1.5, opacity: zen ? 0.06 : 1, transition: 'opacity 1.2s ease' }}>
              <Box sx={{ fontSize: 11.5, fontWeight: 700, color: '#191E26', background: 'rgba(255,255,255,.72)', border: '1px solid rgba(255,255,255,.9)', borderRadius: 9999, px: 1.5, py: 0.5, maxWidth: 210, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {context}
              </Box>
              <Box sx={{ flex: 1 }} />
              <Box component="button" type="button" onClick={() => setZen((z) => !z)} sx={{ border: 'none', background: 'none', color: '#7E8898', fontSize: 11.5, cursor: 'pointer', '&:hover': { color: '#191E26' } }}>
                {zen ? '唤醒' : '渐隐'}
              </Box>
              <Box component="button" type="button" onClick={close} sx={{ border: 'none', background: 'none', color: '#7E8898', fontSize: 11.5, cursor: 'pointer', '&:hover': { color: '#191E26' } }}>
                关闭
              </Box>
            </Box>

            <Box ref={threadRef} className="companion-thread" sx={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 380, overflowY: 'auto', pt: 1, pb: 2 }}>
              {messages.length === 0 ? (
                <Box sx={{ fontSize: 13.5, lineHeight: 1.75, color: '#454E5C', background: 'rgba(255,255,255,.62)', border: '1px solid rgba(255,255,255,.8)', borderRadius: '16px 16px 16px 5px', px: 1.75, py: 1.4, alignSelf: 'flex-start' }}>
                  就「{context}」说吧——它会带着这一条的事实与出处回答。
                </Box>
              ) : (
                messages.map((message, index) => (
                  <Box key={index} sx={{ fontSize: 13.5, lineHeight: 1.75, color: message.me ? '#191E26' : '#454E5C', background: message.me ? 'rgba(214,231,248,.72)' : 'rgba(255,255,255,.62)', border: message.me ? '1px solid rgba(255,255,255,.75)' : '1px solid rgba(255,255,255,.8)', borderRadius: message.me ? '16px 16px 5px 16px' : '16px 16px 16px 5px', px: 1.75, py: 1.4, alignSelf: message.me ? 'flex-end' : 'flex-start', maxWidth: '87%' }}>
                    {message.text}
                  </Box>
                ))
              )}
            </Box>
          </Box>

          {/* 独立输入泡 */}
          <Box className="companion-inputbubble" sx={{ display: 'flex', gap: 8, alignItems: 'center', padding: '8px 8px 8px 20px', background: 'rgba(255,255,255,.5)', backdropFilter: 'blur(26px) saturate(155%)', border: '1px solid rgba(255,255,255,.85)', borderRadius: 9999, boxShadow: 'inset 0 1px 0 rgba(255,255,255,.8), 0 14px 36px rgba(70,95,130,.16)' }}>
            <input
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => { if (event.key === 'Enter') submit(); }}
              placeholder="问它，或说你的想法…"
              style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: 13, color: '#191E26', fontFamily: 'inherit' }}
            />
            <Box component="button" type="button" onClick={submit} sx={{ width: 44, height: 44, borderRadius: '50%', border: 'none', background: '#191E26', color: '#fff', cursor: 'pointer', fontSize: 15, '&:hover': { background: '#0E131B' }, '&:active': { transform: 'scale(.93)' } }}>↑</Box>
          </Box>
        </Box>
      ) : null}
    </Box>,
    document.body,
  );
}
