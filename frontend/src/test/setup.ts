import '@testing-library/jest-dom';

/**
 * Node ≥ 22 暴露了一个实验性的 `localStorage` 全局：没有 `--localstorage-file` 时它的值是
 * undefined。vitest 建立 jsdom 环境、把 jsdom window 的属性挂到 globalThis 时，这个已存在的
 * 全局会把 jsdom 自己那份 localStorage 顶掉——于是测试里 `localStorage` 是 undefined
 * （`Cannot read properties of undefined (reading 'setItem')`），而本机 Node 26 中招生效、
 * CI 的 Node 版本没有这个全局，所以 CI 一直是绿的。
 *
 * 这里只在**缺失**时补一个内存实现：未来 jsdom/vitest 修好这条链路后，这段自动失效。
 * 已确认 jsdom 29 单独使用时 `window.localStorage` 是好的，所以问题不在 jsdom 本身。
 */
function installLocalStorageShim(): void {
  const existing = (globalThis as { localStorage?: Storage }).localStorage;
  if (existing && typeof existing.setItem === 'function') return;

  const store = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return store.size;
    },
    key: (index: number) => [...store.keys()][index] ?? null,
    getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
    setItem: (key: string, value: string) => {
      store.set(String(key), String(value));
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
  };

  Object.defineProperty(globalThis, 'localStorage', {
    value: storage,
    configurable: true,
    writable: true,
  });
  if (typeof window !== 'undefined' && (window as { localStorage?: Storage }).localStorage !== storage) {
    Object.defineProperty(window, 'localStorage', {
      value: storage,
      configurable: true,
      writable: true,
    });
  }
  if (typeof sessionStorage === 'undefined') {
    Object.defineProperty(globalThis, 'sessionStorage', {
      value: storage,
      configurable: true,
      writable: true,
    });
  }
}

installLocalStorageShim();
