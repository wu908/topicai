/**
 * Modal — self-rolled modal mirroring the V3 prototype (topicai-v3-login-meta.html).
 * Replaces MUI Dialog across the app for V3 visual consistency.
 * - Centered overlay with backdrop blur
 * - Sticky header / body / footer
 * - `wide` variant for 720px width
 * - ESC + backdrop click close
 */
import { useEffect, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
}

function Modal({ open, onClose, title, children, footer, wide = false }: ModalProps): ReactNode {
  const overlayRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return createPortal(
    <div
      ref={overlayRef}
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2000,
        background: 'var(--v3-modal-backdrop)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: 'var(--v3-surface)',
          borderRadius: 'var(--v3-radius-lg)',
          width: wide ? 720 : 560,
          maxWidth: '92vw',
          maxHeight: '82vh',
          overflowY: 'auto',
          boxShadow: 'var(--v3-shadow-modal)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '20px 24px 14px',
            borderBottom: '1px solid var(--v3-border-light)',
            position: 'sticky',
            top: 0,
            background: 'var(--v3-surface)',
            zIndex: 1,
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{title}</h3>
          <button
            onClick={onClose}
            aria-label="关闭"
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: 16,
              color: 'var(--v3-text-sec)',
              display: 'grid',
              placeItems: 'center',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--v3-overlay-3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            ✕
          </button>
        </div>
        <div style={{ padding: '20px 24px', flex: 1 }}>{children}</div>
        {footer ? (
          <div
            style={{
              padding: '14px 24px',
              borderTop: '1px solid var(--v3-border-light)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8,
              background: 'var(--v3-surface)',
              position: 'sticky',
              bottom: 0,
            }}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}

export default Modal;
