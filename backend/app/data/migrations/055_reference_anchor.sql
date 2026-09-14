-- 055_reference_anchor.sql（冷启动锚点 R7）
--
-- 「你想做成什么样」——从用户贴的参考样本里读出来的方向，与「你是谁」的画像
-- (creator_profiles) 刻意分开放。
--
-- 为什么必须分开：画像回答"你是谁"，参考回答"你想成为谁"。把后者的结论写进前者的列，
-- 系统就会对刚注册的用户说"你的定位是别人的定位"——那是他在冷启动阶段最无法反驳的
-- 一句话（隔离不变式见 tests/services/test_reference_samples.py）。
--
-- capability='user_edited' 是不可逆的：用户改过之后，参考集再变化也不覆盖他的判断。
-- 参考样本可以影响"你想成为谁"，但用户说什么就是什么。
CREATE TABLE IF NOT EXISTS reference_anchors (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL UNIQUE,
    topics_json TEXT NOT NULL DEFAULT '[]',
    structure_habits_json TEXT NOT NULL DEFAULT '[]',
    audience_json TEXT,
    rejected_json TEXT NOT NULL DEFAULT '[]',
    source_handles_json TEXT NOT NULL DEFAULT '[]',
    reference_note_count INTEGER NOT NULL DEFAULT 0 CHECK (reference_note_count >= 0),
    capability TEXT NOT NULL
        CHECK (capability IN ('structured_llm','deterministic_fallback','user_edited')),
    limitations_json TEXT NOT NULL DEFAULT '[]',
    ai_trace_id TEXT,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
);
