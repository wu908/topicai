/**
 * 把用户粘进来的一段文字拆成参考样本（冷启动锚点 R7）。
 *
 * 设计取向：**不让用户学格式**。用户是从小红书复制出来的，不是填表的。
 * 所以规则只有两条："空行分隔多条"、"第一条以 @ 或「来源」开头就是来源"，
 * 其余全部当成标题与正文。识别结果立刻回显给用户看（见页面里的预览）——
 * 让他自己确认我们读对了，而不是提交后才发现格式错了。
 */

export interface ParsedReference {
  source_handle: string;
  title: string;
  body_excerpt: string;
  tags: string[];
}

export interface ParsedReferences {
  items: ParsedReference[];
  /** 人话描述的问题，逐条对应；有内容时提交按钮不可用。 */
  problems: string[];
}

/** 「来源：xxx」这种前缀要去掉；「@xxx」保留 @——读数里直接显示成"参考来自：@甲"。 */
const EXPLICIT_SOURCE_PREFIX = /^来源[:：]?\s*/;

export function parseReferences(value: string): ParsedReferences {
  const blocks = value
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean);
  const items: ParsedReference[] = [];
  const problems: string[] = [];

  blocks.forEach((block, index) => {
    const lines = block
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    const first = lines[0] ?? '';
    const hasHandle = first.startsWith('@') || EXPLICIT_SOURCE_PREFIX.test(first);
    const handle = hasHandle
      ? first.startsWith('@')
        ? first
        : first.replace(EXPLICIT_SOURCE_PREFIX, '').trim()
      : '';
    const rest = hasHandle ? lines.slice(1) : lines;
    const title = rest[0] ?? '';
    if (!title) {
      problems.push(`第 ${index + 1} 条只有来源，没有标题或正文`);
      return;
    }
    if (!handle) problems.push(`第 ${index + 1} 条没写来源（在第一行加 @账号名）`);
    items.push({
      source_handle: handle,
      title: title.slice(0, 200),
      body_excerpt: rest.slice(1).join('\n').slice(0, 5000),
      tags: [],
    });
  });

  return { items, problems };
}

/** 1 条只能看出方向，2 条以上才看得出规律——把阈值说出来，而不是让用户猜。 */
export function referenceCountHint(count: number): string {
  if (count === 0) return '';
  if (count === 1) return '1 条只能看出方向；再贴 1 条才看得出规律';
  return `${count} 条参考：读出来的方向会作为候选规律，而不是定论`;
}
