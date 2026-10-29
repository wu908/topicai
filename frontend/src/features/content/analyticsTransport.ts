/**
 * First-party analytics 上报（A3 v2 §4）。
 *
 * 默认关闭（`VITE_ANALYTICS_ENABLED !== 'true'` 时不入队、不发请求）；
 * 队列上限 200；≥20 条或每 5s flush；分片 ≤32 条且序列化 ≤48KB；
 * pagehide 在同一同步 tick 发起所有分片（keepalive，不逐片 await）；
 * in-flight 防双发；队列溢出丢最旧；任一分片失败即停发后续分片（丢弃、不重试）；
 * 401/503/429/网络错误一律丢弃并 console.debug，不抛错、不强制登出。
 *
 * 不复用 `services/api/client.ts`：那里 401 会 refresh/forceLogout，埋点不能影响主流程。
 * 不采集：页面内容、用户输入、token、URL query；payload 由调用方按白名单给稳定键。
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
export const ANALYTICS_EVENTS_ENDPOINT = `${API_BASE_URL}/api/v2/analytics/events`;

export const ANALYTICS_QUEUE_LIMIT = 200;
const FLUSH_THRESHOLD = 20;
const FLUSH_INTERVAL_MS = 5_000;
const MAX_EVENTS_PER_CHUNK = 32;
const MAX_CHUNK_BYTES = 48 * 1024;

export type AnalyticsPayload = Record<string, string | number | boolean | null>;

export interface AnalyticsEvent {
  event: string;
  payload: AnalyticsPayload;
  client_ts: string;
  idem_key: string;
}

/** 总开关：默认 false（A9-20261030-04 用户签字前不得采集）。 */
export const enabled: boolean = import.meta.env.VITE_ANALYTICS_ENABLED === 'true';

const queue: AnalyticsEvent[] = [];
let flushTimer: ReturnType<typeof setInterval> | null = null;
let flushTimeout: ReturnType<typeof setTimeout> | null = null;
let flushing = false;

function debug(message: string): void {
  console.debug(`[analytics] ${message}`);
}

function newIdemKey(): string {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
  } catch {
    // 旧 WebView / 部分测试环境没有 randomUUID：走下面的 fallback
  }
  return `idem-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function byteLength(text: string): number {
  return typeof TextEncoder === 'undefined' ? text.length : new TextEncoder().encode(text).length;
}

function readAccessToken(): string | null {
  try {
    return localStorage.getItem('access_token');
  } catch {
    return null; // 隐私模式 / 无 storage 环境
  }
}

function buildBody(events: AnalyticsEvent[]): string {
  return JSON.stringify({ events });
}

/** 按 ≤32 条且序列化 ≤48KB 切分；单条超限时自成一“片”，由服务端 413 丢弃。 */
function splitIntoChunks(events: AnalyticsEvent[]): AnalyticsEvent[][] {
  const chunks: AnalyticsEvent[][] = [];
  let current: AnalyticsEvent[] = [];
  for (const item of events) {
    const candidate = [...current, item];
    const fits =
      candidate.length <= MAX_EVENTS_PER_CHUNK && byteLength(buildBody(candidate)) <= MAX_CHUNK_BYTES;
    if (current.length > 0 && !fits) {
      chunks.push(current);
      current = [item];
    } else {
      current = candidate;
    }
  }
  if (current.length > 0) chunks.push(current);
  return chunks;
}

/** 从队列头部取一片（就地移除），保证 in-flight 中的事件不会再被第二次发送。 */
function takeChunk(): AnalyticsEvent[] {
  const chunk: AnalyticsEvent[] = [];
  while (queue.length > 0) {
    const candidate = [...chunk, queue[0]];
    const fits =
      candidate.length <= MAX_EVENTS_PER_CHUNK && byteLength(buildBody(candidate)) <= MAX_CHUNK_BYTES;
    if (chunk.length > 0 && !fits) break;
    chunk.push(queue.shift()!);
  }
  return chunk;
}

/** 单片 POST；返回 false 时调用方丢弃该片及其后续（不重试）。 */
async function sendChunk(events: AnalyticsEvent[], keepalive: boolean): Promise<boolean> {
  const token = readAccessToken();
  if (!token) {
    debug('drop chunk: no access_token');
    return false;
  }
  try {
    const response = await fetch(ANALYTICS_EVENTS_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: buildBody(events),
      keepalive,
    });
    if (!response.ok) {
      // 401/413/422/429/503 都是“这一片不要了”，不 refresh、不重试、不抛错
      debug(`drop chunk: HTTP ${response.status}`);
      return false;
    }
    return true;
  } catch {
    debug('drop chunk: network error');
    return false;
  }
}

function stopTimer(): void {
  if (flushTimer !== null) {
    clearInterval(flushTimer);
    flushTimer = null;
  }
}

function ensureTimer(): void {
  if (flushTimer !== null) return;
  flushTimer = setInterval(() => {
    void flushAnalytics();
  }, FLUSH_INTERVAL_MS);
}

function scheduleFlush(): void {
  if (flushTimeout !== null || flushing) return;
  // 阈值到达后放到下一宏任务：同一 burst 的其余事件进同一批；pagehide 时仍可直接发整队。
  flushTimeout = setTimeout(() => {
    flushTimeout = null;
    void flushAnalytics();
  }, 0);
}

function cancelScheduledFlush(): void {
  if (flushTimeout !== null) {
    clearTimeout(flushTimeout);
    flushTimeout = null;
  }
}

/** 入队一条事件；开关关闭时静默丢弃（不入队、不调度）。 */
export function queueEvent(event: string, payload: AnalyticsPayload): void {
  if (!enabled) return;
  queue.push({ event, payload, client_ts: new Date().toISOString(), idem_key: newIdemKey() });
  if (queue.length > ANALYTICS_QUEUE_LIMIT) {
    queue.splice(0, queue.length - ANALYTICS_QUEUE_LIMIT); // 超上限丢最旧
  }
  ensureTimer();
  if (queue.length >= FLUSH_THRESHOLD) scheduleFlush();
}

/** 逐片发送当前队列；in-flight 时直接返回（不重复发同一片）。 */
export async function flushAnalytics(): Promise<void> {
  if (!enabled || flushing || queue.length === 0) return;
  flushing = true;
  try {
    while (queue.length > 0) {
      const chunk = takeChunk();
      const ok = await sendChunk(chunk, false);
      if (!ok) {
        queue.length = 0; // 任一分片失败：停发后续分片，已排队事件一并丢弃（不重试）
        break;
      }
    }
  } finally {
    flushing = false;
    if (queue.length === 0) stopTimer();
    else if (queue.length >= FLUSH_THRESHOLD) scheduleFlush();
  }
}

/**
 * pagehide：清定时器后在同一同步 tick 发起所有分片（keepalive，不逐片 await）。
 * “失败停发后续”只约束定时/阈值 flush；此处页面即将卸载，接受 keepalive 聚合预算外的丢弃。
 */
function handlePageHide(): void {
  if (!enabled) return;
  cancelScheduledFlush();
  stopTimer();
  if (queue.length === 0) return;
  const chunks = splitIntoChunks(queue.splice(0, queue.length));
  for (const chunk of chunks) {
    void sendChunk(chunk, true);
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('pagehide', handlePageHide);
}

/** 仅供测试/调试：当前待发送事件数。 */
export function pendingEventCount(): number {
  return queue.length;
}

/** 仅供测试/调试：清空队列、定时器与 in-flight 标记。 */
export function resetAnalyticsTransport(): void {
  queue.length = 0;
  flushing = false;
  cancelScheduledFlush();
  stopTimer();
}
