/**
 * T-FE-1..6（A4 v2 §2）：analyticsTransport 队列/分片/pagehide/in-flight/失败静默/默认关闭。
 * 通过 vi.stubEnv + resetModules 按开关重新加载模块，模拟“构建时 env”的取值。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type Transport = typeof import('../analyticsTransport');

const loadedModules: Transport[] = [];
let fetchMock: ReturnType<typeof vi.fn>;

async function loadTransport(flag?: string): Promise<Transport> {
  vi.resetModules();
  if (flag === undefined) vi.unstubAllEnvs();
  else vi.stubEnv('VITE_ANALYTICS_ENABLED', flag);
  const module = (await import('../analyticsTransport')) as Transport;
  loadedModules.push(module);
  return module;
}

function response(status: number): Response {
  return new Response('{}', { status, headers: { 'Content-Type': 'application/json' } });
}

function byteLength(value: string): number {
  return new TextEncoder().encode(value).length;
}

function bodies(): Array<Array<{ event: string; payload: Record<string, unknown>; idem_key: string }>> {
  return fetchMock.mock.calls.map((call) => {
    const init = call[1] as RequestInit;
    return JSON.parse(init.body as string).events;
  });
}

function queueMany(transport: Transport, count: number): void {
  for (let i = 0; i < count; i += 1) {
    transport.queueEvent('content_list_view', { group: 'all', count: i });
  }
}

/** 推进 fake timers 并排空 flush 内部的微任务链。 */
async function tick(ms = 0): Promise<void> {
  await vi.advanceTimersByTimeAsync(ms);
  for (let i = 0; i < 12; i += 1) await Promise.resolve();
}

beforeEach(() => {
  vi.useFakeTimers();
  localStorage.setItem('access_token', 'test-token');
  fetchMock = vi.fn().mockResolvedValue(response(200));
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  for (const module of loadedModules) module.resetAnalyticsTransport();
  loadedModules.length = 0;
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.useRealTimers();
  localStorage.clear();
});

describe('analyticsTransport（A3 §4）', () => {
  it('T-FE-1: 队列 ≥20 条触发 flush，分片 ≤32 条', async () => {
    const transport = await loadTransport('true');
    expect(transport.enabled).toBe(true);

    queueMany(transport, 20);
    expect(transport.pendingEventCount()).toBe(20);
    expect(fetchMock).not.toHaveBeenCalled();

    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(bodies()[0]).toHaveLength(20);
    // 请求体形状与契约一致（03-api-contract §1）
    expect(Object.keys(bodies()[0][0]).sort()).toEqual(['client_ts', 'event', 'idem_key', 'payload']);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/v2/analytics/events');
    expect(init.method).toBe('POST');
    expect(init.headers).toMatchObject({ Authorization: 'Bearer test-token' });

    // 40 条 → 32 + 8 两片
    queueMany(transport, 40);
    await tick();
    const split = bodies().slice(1);
    expect(split.length).toBeGreaterThan(1);
    expect(split.every((chunk) => chunk.length <= 32)).toBe(true);
    expect(split.reduce((sum, chunk) => sum + chunk.length, 0)).toBe(40);
  });

  it('T-FE-1: 不足 20 条时每 5s flush', async () => {
    const transport = await loadTransport('true');
    queueMany(transport, 3);
    expect(fetchMock).not.toHaveBeenCalled();

    await tick(5_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(bodies()[0]).toHaveLength(3);
  });

  it('T-FE-1: 分片同时受序列化 ≤48KB 限制', async () => {
    const transport = await loadTransport('true');
    // 合成大 payload 只为压到 48KB 分片上限；真实事件按白名单 ≤1KB。
    for (let i = 0; i < 32; i += 1) {
      transport.queueEvent('content_list_view', { group: 'all', count: i, padding: 'x'.repeat(1500) });
    }
    await transport.flushAnalytics();

    const chunks = bodies();
    expect(chunks.length).toBeGreaterThan(1);
    for (const chunk of chunks) {
      expect(chunk.length).toBeLessThanOrEqual(32);
      expect(byteLength(JSON.stringify({ events: chunk }))).toBeLessThanOrEqual(48 * 1024);
    }
    expect(chunks.reduce((sum, chunk) => sum + chunk.length, 0)).toBe(32);
  });

  it('队列超 200 丢最旧', async () => {
    const transport = await loadTransport('true');
    queueMany(transport, 205);
    expect(transport.pendingEventCount()).toBe(200);

    await transport.flushAnalytics();
    const events = bodies().flat();
    expect(events).toHaveLength(200);
    expect(events[0].payload).toMatchObject({ count: 5 }); // 丢弃 count 0–4
    expect(events[events.length - 1].payload).toMatchObject({ count: 204 });
  });

  it('T-FE-2: 队列 200 时 pagehide 在同一同步 tick 发起所有分片（keepalive）', async () => {
    const transport = await loadTransport('true');
    queueMany(transport, 200);
    expect(transport.pendingEventCount()).toBe(200);
    expect(fetchMock).not.toHaveBeenCalled();

    window.dispatchEvent(new Event('pagehide'));

    // dispatchEvent 返回时所有分片已经发起：不是逐片 await 后再发下一片。
    const calls = fetchMock.mock.calls as Array<[string, RequestInit]>;
    expect(calls).toHaveLength(7); // ceil(200 / 32)
    expect(calls.every((call) => call[1].keepalive === true)).toBe(true);
    const sizes = bodies().map((chunk) => chunk.length);
    expect(sizes.every((size) => size <= 32)).toBe(true);
    expect(sizes.reduce((sum, size) => sum + size, 0)).toBe(200);
    expect(transport.pendingEventCount()).toBe(0);

    // pagehide 已清定时器：之后不会再补发。
    await tick(6_000);
    expect(fetchMock).toHaveBeenCalledTimes(7);
  });

  it('T-FE-3: in-flight 防双发（同一片未完成不重复发送）', async () => {
    const transport = await loadTransport('true');
    let release: (value: Response) => void = () => {};
    fetchMock.mockImplementationOnce(
      () => new Promise<Response>((resolve) => { release = resolve; })
    );

    queueMany(transport, 20);
    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    // 第一片未完成时又入队 20 条：定时器 flush 与手动 flush 都不得重复发同一片。
    queueMany(transport, 20);
    await tick();
    await transport.flushAnalytics();
    await Promise.resolve();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(transport.pendingEventCount()).toBe(20);

    release(response(200));
    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(2);

    const idemKeys = bodies().flat().map((event) => event.idem_key);
    expect(idemKeys).toHaveLength(40);
    expect(new Set(idemKeys).size).toBe(40); // 没有任何事件被重复发送
  });

  it.each([401, 503, 429])('T-FE-4: HTTP %i 丢弃且不抛错', async (status) => {
    const transport = await loadTransport('true');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    fetchMock.mockResolvedValue(response(status));

    queueMany(transport, 20);
    await tick();
    await expect(transport.flushAnalytics()).resolves.toBeUndefined();
    expect(transport.pendingEventCount()).toBe(0);
    expect(debugSpy).toHaveBeenCalledWith(expect.stringContaining(`HTTP ${status}`));
    debugSpy.mockRestore();
  });

  it('T-FE-4: 网络错误丢弃且不抛错', async () => {
    const transport = await loadTransport('true');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    fetchMock.mockRejectedValue(new TypeError('network down'));

    queueMany(transport, 20);
    await tick();
    await expect(transport.flushAnalytics()).resolves.toBeUndefined();
    expect(transport.pendingEventCount()).toBe(0);
    expect(debugSpy).toHaveBeenCalledWith(expect.stringContaining('network error'));
    debugSpy.mockRestore();
  });

  it('T-FE-4: 任一分片失败即停发后续分片', async () => {
    const transport = await loadTransport('true');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    fetchMock.mockResolvedValue(response(503));

    queueMany(transport, 40); // 32 + 8 两片
    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(1); // 第一片失败后不再发第二片
    expect(transport.pendingEventCount()).toBe(0); // 失败即丢弃，不重试
    debugSpy.mockRestore();
  });

  it('无 access_token 时丢弃（不惊动 client.ts 的强制登出）', async () => {
    const transport = await loadTransport('true');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    localStorage.removeItem('access_token');

    queueMany(transport, 3);
    await transport.flushAnalytics();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(transport.pendingEventCount()).toBe(0);
    expect(debugSpy).toHaveBeenCalledWith(expect.stringContaining('no access_token'));
    debugSpy.mockRestore();
  });

  it('localStorage 读取抛错时丢弃且不抛错', async () => {
    const transport = await loadTransport('true');
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('storage blocked');
      },
    });

    queueMany(transport, 3);
    await expect(transport.flushAnalytics()).resolves.toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(transport.pendingEventCount()).toBe(0);
  });

  it('T-FE-5: 开关显式 false 时不入队', async () => {
    const transport = await loadTransport('false');
    expect(transport.enabled).toBe(false);

    queueMany(transport, 25);
    expect(transport.pendingEventCount()).toBe(0);
    await tick(6_000);
    await transport.flushAnalytics();
    window.dispatchEvent(new Event('pagehide'));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('T-FE-6: 无 env 时默认关闭（VITE_ANALYTICS_ENABLED 缺省 false）', async () => {
    vi.unstubAllEnvs();
    const transport = await loadTransport(undefined);
    expect(transport.enabled).toBe(false);

    queueMany(transport, 25);
    expect(transport.pendingEventCount()).toBe(0);
    await tick(6_000);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('幂等键：randomUUID 不可用时回退为 8–64 字符', async () => {
    const transport = await loadTransport('true');
    vi.stubGlobal('crypto', { getRandomValues: (array: Uint8Array) => array });

    queueMany(transport, 1);
    await transport.flushAnalytics();

    const [event] = bodies()[0];
    expect(event.idem_key).toMatch(/^idem-/);
    expect(event.idem_key.length).toBeGreaterThanOrEqual(8);
    expect(event.idem_key.length).toBeLessThanOrEqual(64);
  });
});
