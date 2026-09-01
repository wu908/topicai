/** 轴向入口：任意界面调用它注入上下文并打开悬浮球对话（DESIGN.md v3 §6） */
export function openCompanion(context: string): void {
  window.dispatchEvent(new CustomEvent('topicai:companion-open', { detail: { context } }));
}
