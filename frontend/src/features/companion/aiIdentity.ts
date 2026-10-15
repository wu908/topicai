/**
 * 双 AI 身份：全局助手 / 项目助手 分开存。
 * 即改即存（localStorage）；实现阶段可换为 /api/v2/settings。
 */
export type AiIdentity = {
  name: string;
  /** data URL 或空；空则用 letter + gradient */
  avatar: string | null;
  /** 光晕色 key，无图时使用 */
  tone: 'a' | 'b' | 'c' | 'd';
};

export type AiIdentities = {
  global: AiIdentity;
  project: AiIdentity;
};

const KEY = 'topicai.ai-identities.v1';

export const defaultIdentities: AiIdentities = {
  global: { name: '阿洛', avatar: null, tone: 'a' },
  project: { name: '项目助手', avatar: null, tone: 'c' },
};

const toneStyles: Record<AiIdentity['tone'], string> = {
  a: 'radial-gradient(circle at 32% 28%, #fff, rgba(143,190,232,0.55) 60%, rgba(143,190,232,0.2))',
  b: 'radial-gradient(circle at 32% 28%, #fff, rgba(201,138,75,0.5) 60%, rgba(201,138,75,0.18))',
  c: 'radial-gradient(circle at 32% 28%, #fff, rgba(143,190,232,0.32) 60%, rgba(25,30,38,0.08))',
  d: 'radial-gradient(circle at 32% 28%, #fff, rgba(25,30,38,0.22) 60%, rgba(25,30,38,0.08))',
};

export function avatarStyle(id: AiIdentity): string {
  if (id.avatar) {
    return `center/cover no-repeat url(${id.avatar})`;
  }
  return toneStyles[id.tone] || toneStyles.a;
}

export function avatarLetter(id: AiIdentity): string {
  const n = (id.name || 'A').trim();
  return n.slice(0, 1).toUpperCase();
}

export function loadIdentities(): AiIdentities {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return { ...defaultIdentities };
    const parsed = JSON.parse(raw) as Partial<AiIdentities>;
    return {
      global: { ...defaultIdentities.global, ...(parsed.global || {}) },
      project: { ...defaultIdentities.project, ...(parsed.project || {}) },
    };
  } catch {
    return { ...defaultIdentities };
  }
}

export function saveIdentities(next: AiIdentities): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // storage full / private mode — 会话内仍可用
  }
}

export function updateIdentity(
  which: keyof AiIdentities,
  patch: Partial<AiIdentity>,
): AiIdentities {
  const cur = loadIdentities();
  const next: AiIdentities = {
    ...cur,
    [which]: { ...cur[which], ...patch },
  };
  saveIdentities(next);
  return next;
}

type Listener = () => void;
const listeners = new Set<Listener>();

export function subscribeIdentities(fn: Listener): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function notifyIdentities(): void {
  listeners.forEach((fn) => fn());
}
