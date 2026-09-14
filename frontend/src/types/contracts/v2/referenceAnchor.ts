/** 「你想做成什么样」——从参考样本读出来的方向（冷启动锚点 R7）。 */

export interface AnchorItem {
  value: string;
  /** 支撑这条结论的参考样本 id（reference_note:<id>）。 */
  evidence_refs: string[];
  /** 由几条参考支撑——决定 confidence，不是模型口气决定。 */
  sample_count: number;
  confidence: 'low' | 'medium' | 'high';
  limitations: string[];
}

export type AnchorCapability = 'structured_llm' | 'deterministic_fallback' | 'user_edited';

export interface ReferenceAnchor {
  reference_count: number;
  source_handles: string[];
  topics: AnchorItem[];
  structure_habits: AnchorItem[];
  audience: AnchorItem | null;
  rejected: string[];
  capability: AnchorCapability;
  limitations: string[];
  version: number;
  updated_at: string;
}

export interface ReferenceNoteInput {
  title: string;
  body_excerpt?: string;
  tags?: string[];
  source_handle: string;
}

export interface ReferenceAnchorUpdate {
  /** 否证掉的结论：不再出现，但系统继续从参考里读。 */
  rejected?: string[];
  /** 自己重写的内容：填了就以此为准，之后不再自动重推。 */
  topics?: string[];
  structure_habits?: string[];
  audience?: string;
  expected_version: number;
}
