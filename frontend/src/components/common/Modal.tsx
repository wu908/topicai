/**
 * Modal — self-rolled modal mirroring the V3 prototype (topicai-v3-login-meta.html).
 * Replaces MUI Dialog across the app for V3 visual consistency.
 * - Centered overlay with backdrop blur
 * - Sticky header / body / footer (overflowY moved to body)
 * - `wide` variant for 720px width
 * - ESC + backdrop click close
 * - Focus trap with active-outside fallback
 * - Focus restore on close
 * - role="dialog" + aria-modal + aria-labelledby
 * - Body scroll lock via refcount (stacked modals safe)
 *
 * Note for callers: `onClose` does not need useCallback — this component
 * stores it in a ref and re-binds listeners only when `open` flips.
 */
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Body scroll lock refcount — shared across all Modal instances on the page.
let bodyLockCount = 0;
let bodyLockPrevOverflow = '';

function acquireBodyLock(): void {
  if (bodyLockCount === 0) {
    bodyLockPrevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }
  bodyLockCount += 1;
}

function releaseBodyLock(): void {
  if (bodyLockCount === 0) return;
  bodyLockCount -= 1;
  if (bodyLockCount === 0) {
    document.body.style.overflow = bodyLockPrevOverflow;
    bodyLockPrevOverflow = '';
  }
}

function Modal({ open, onClose, title, children, footer, wide = false }: ModalProps): ReactNode {
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const closeBtnRef = useRef<HTMLButtonElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const titleId = useId();

  // Stash onClose in a ref so the open/close effect can depend only on [open].
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        onCloseRef.current();
        return;
      }
      if (e.key === 'Tab') {
        const overlay = overlayRef.current;
        if (!overlay) return;
        const focusables = Array.from(
          overlay.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
        );
        if (focusables.length === 0) {
          e.preventDefault();
          return;
        }
        const first = focusables[0]!;
        const last = focusables[focusables.length - 1]!;
        const active = document.activeElement as HTMLElement | null;

        // If focus has somehow escaped the dialog, force it back to first.
        if (!active || !overlay.contains(active)) {
          e.preventDefault();
          first.focus();
          return;
        }
        if (e.shiftKey && active === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && active === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);

    previousFocusRef.current = document.activeElement as HTMLElement | null;
    acquireBodyLock();

    // Defer focus to next tick so React has rendered the modal content.
    const focusTimer = window.setTimeout(() => {
      closeBtnRef.current?.focus();
    }, 0);

    return () => {
      document.removeEventListener('keydown', onKey);
      releaseBodyLock();
      window.clearTimeout(focusTimer);
      const prev = previousFocusRef.current;
      if (prev && typeof prev.focus === 'function') {
        prev.focus();
      }
    };
  }, [open]);

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
        WebkitBackdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={{
          background: 'var(--v3-surface)',
          borderRadius: 'var(--v3-radius-lg)',
          width: wide ? 720 : 560,
          maxWidth: '92vw',
          maxHeight: '82vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--v3-shadow-modal)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '20px 24px 14px',
            borderBottom: '1px solid var(--v3-border-light)',
            background: 'var(--v3-surface)',
          }}
        >
          <h3 id={titleId} style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>
            {title}
          </h3>
          <button
            ref={closeBtnRef}
            type="button"
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
        <div style={{ padding: '20px 24px', flex: 1, overflowY: 'auto' }}>{children}</div>
        {footer ? (
          <div
            style={{
              padding: '14px 24px',
              borderTop: '1px solid var(--v3-border-light)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8,
              background: 'var(--v3-surface)',
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
