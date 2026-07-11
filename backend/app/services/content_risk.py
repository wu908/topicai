"""Content risk detection service for TopicAI v4.0.

Scans content for compliance risks including platform policy violations,
copyright issues, and sensitive keywords.

Spec-007 US5 (T075): explicit 80/20 keyword+LLM blend per FR-008 and
Constitution Principle XI (Hybrid AI Discipline).

Algorithm (when LLM gate is open, i.e. keyword confidence < threshold):
  1. keyword_scan -> (risks_kw, score_kw, conf_kw)            # 80% weight
  2. try: llm_enhance -> (risks_llm, score_llm, conf_llm)     # 20% weight
     except: log warning + fall back to 100% keyword path
  3. final_score  = 0.8 * score_kw + 0.2 * score_llm
     final_risks  = union(keyword_risks, llm_risks) deduped
     final_confid = max(keyword_conf, 0.75) for LLM-succeeded path,
                    min(keyword_conf, 0.5)  for keyword-only fallback
  4. data_source  = "llm_simulation" if LLM succeeded else "keyword_only"

Keyword source (T401-T405): when a ``db`` is injected, the keyword list
is read from the ``risk_keywords`` table (seeded from
``app/data/seed/risk_keywords.json`` on first use), with per-user rows
overriding global rows of the same keyword. Without a db, the legacy
hardcoded ``_RISKY_KEYWORDS`` list is the fallback so existing
test/mock paths keep working.

Constitution III: every response carries confidence / data_source /
model_version.
Constitution VI: heuristic-first; LLM only when keyword confidence is
low OR on the explicit 80/20 path. Any LLM failure must NOT propagate.
"""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.utils import utc_now

logger = logging.getLogger(__name__)


# Risk keyword catalog: (keyword, severity, category).
# Higher-precision financial/medical terms added per spec-007 T069/T070.
_RISKY_KEYWORDS: list[tuple[str, str, str]] = [
    # Financial inducement (US5 T069)
    ("保本", "high", "financial_inducement"),
    ("无风险", "high", "financial_inducement"),
    ("guaranteed no loss", "high", "financial_inducement"),
    ("稳赚不赔", "high", "financial_inducement"),
    ("高收益无风险", "high", "financial_inducement"),
    # Medical overclaim (US5 T070)
    ("100% 治愈", "high", "medical_overclaim"),
    ("100% cure", "high", "medical_overclaim"),
    ("包治百病", "high", "medical_overclaim"),
    ("根治", "high", "medical_overclaim"),
    ("彻底治愈", "high", "medical_overclaim"),
    # Regulatory (kept from prior implementation)
    ("赌博", "high", "gambling"),
    ("色情", "high", "pornography"),
    ("违法", "high", "illegal"),
    ("诈骗", "high", "fraud"),
    ("传销", "high", "fraud"),
    ("暴力", "high", "violence"),
    # Medium
    ("绝对", "medium", "absolute_claim"),
    ("保证", "medium", "absolute_claim"),
    ("100%", "medium", "absolute_claim"),
    ("点击领取", "medium", "clickbait"),
    # Low
    ("最", "low", "superlative"),
    ("第一", "low", "superlative"),
    ("最好", "low", "superlative"),
    ("唯一", "low", "superlative"),
    ("全网", "low", "superlative"),
]

# Confidence threshold below which the LLM path is consulted.
_LLM_CONFIDENCE_THRESHOLD = 0.6
_LLM_MODEL_VERSION = "deepseek-v4-flash"
_KEYWORD_MODEL_VERSION = "keyword-v1"

# 80/20 blend weights per FR-008 (US5 T075). Note: the FR-008 spec inverts
# the original 20/80 LLM-heavy direction — keyword scan is the dominant
# signal, the LLM only refines the score.
_KEYWORD_BLEND_WEIGHT = 0.8
_LLM_BLEND_WEIGHT = 0.2

# Confidence caps (Constitution III/VI).
_LLM_CONFIDENCE = 0.75         # reported when LLM path succeeds
_KEYWORD_ONLY_CONFIDENCE_CAP = 0.5  # reported on keyword-only fallback


class ContentRiskService:
    """Content compliance risk scanner.

    Heuristic keyword scan is the primary signal; the LLM is invoked when
    the keyword confidence is below ``_LLM_CONFIDENCE_THRESHOLD`` and the
    two are blended at 80% (keyword) + 20% (LLM) per FR-008.

    Args:
        db: Optional ``Database`` instance. When provided, the keyword
            library is read from the ``risk_keywords`` table (seeded
            lazily on first ``check()`` from
            ``app/data/seed/risk_keywords.json``); per-user rows for the
            same keyword override the global entry. When ``None``, the
            hardcoded ``_RISKY_KEYWORDS`` list is used as a fallback so
            the service stays usable in tests / scripts that don't wire
            a database.
    """

    def __init__(self, db: Any | None = None):
        self.db = db
        # Once-loaded guard for the seed. We can't reuse asyncio.Lock
        # across event loops, so we lazily create one per instance.
        self._seed_loaded = False
        self._load_lock: asyncio.Lock | None = None

    # ---------------- seed loader (T402) ----------------

    def _ensure_lock(self) -> asyncio.Lock | None:
        """Return the per-instance lock, or None if no db is wired in."""
        if self.db is None:
            return None
        if self._load_lock is None:
            self._load_lock = asyncio.Lock()
        return self._load_lock

    async def _load_seed_if_needed(self) -> None:
        """Idempotently seed the global risk_keywords rows from JSON.

        Behaviour:
        * If ``self.db`` is ``None`` this is a no-op (hardcoded fallback).
        * If the global keyword count is already > 0, do nothing.
        * Otherwise, load ``app/data/seed/risk_keywords.json`` and INSERT
          each entry with ``user_id IS NULL``.

        The (user_id, keyword) UNIQUE index treats NULL != NULL in SQLite,
        so a plain ``INSERT OR IGNORE`` cannot dedupe the global seed —
        we instead guard with a count check + an ``asyncio.Lock`` to make
        a concurrent first-call race-safe.
        """
        if self.db is None:
            return
        if self._seed_loaded:
            return
        lock = self._ensure_lock()
        if lock is not None:
            async with lock:
                if self._seed_loaded:
                    return
                await self._do_load_seed()
                self._seed_loaded = True
        else:
            await self._do_load_seed()
            self._seed_loaded = True

    async def _do_load_seed(self) -> None:
        """Perform the actual seed INSERT (called under the lock)."""
        assert self.db is not None
        count_row = await self.db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM risk_keywords WHERE user_id IS NULL"
        )
        existing = int((count_row or {}).get("cnt", 0) or 0)
        if existing > 0:
            return

        seed_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "seed"
            / "risk_keywords.json"
        )
        try:
            with open(seed_path, encoding="utf-8") as fh:
                seed_entries = json.load(fh)
        except FileNotFoundError:
            logger.warning(
                "risk: seed file missing at %s — skipping seed load", seed_path
            )
            return
        except (OSError, ValueError) as e:
            logger.warning(
                "risk: failed to read seed file %s: %s — skipping seed load",
                seed_path,
                e,
            )
            return

        now_iso = utc_now()
        for entry in seed_entries:
            if not isinstance(entry, dict):
                continue
            keyword = entry.get("keyword")
            severity = entry.get("severity")
            category = entry.get("category")
            if not keyword or not severity or not category:
                continue
            await self.db.insert(
                "risk_keywords",
                {
                    "id": str(uuid.uuid4()),
                    "user_id": None,
                    "keyword": keyword,
                    "severity": severity,
                    "category": category,
                    "created_at": now_iso,
                },
            )
        logger.info("risk: seeded %d global risk_keywords rows", len(seed_entries))

    # ---------------- keyword fetch (T403/T404) ----------------

    async def _fetch_keywords(
        self, user_id: str
    ) -> list[tuple[str, str, str]] | None:
        """Read the effective keyword set for ``user_id`` from the db.

        Returns ``None`` when no db is wired in (caller should use the
        hardcoded fallback). Per-user rows override the global row of the
        same keyword for that user only.

        Returns:
            List of (keyword, severity, category) tuples, or None.
        """
        if self.db is None:
            return None
        rows = await self.db.fetch_all(
            "SELECT keyword, severity, category, user_id "
            "FROM risk_keywords WHERE user_id IS NULL OR user_id = :uid",
            {"uid": user_id},
        )
        # Per-user override takes precedence over global.
        by_keyword: dict[str, tuple[str, str, str]] = {}
        for row in rows:
            kw = row.get("keyword")
            if kw is None:
                continue
            entry = (
                str(kw),
                str(row.get("severity", "low")),
                str(row.get("category", "")),
            )
            existing = by_keyword.get(kw)
            if existing is None:
                by_keyword[kw] = entry
            elif row.get("user_id") is not None:
                # User-specific row replaces the global one.
                by_keyword[kw] = entry
        return list(by_keyword.values())

    # ---------------- keyword scan ----------------

    def _scan_risk(
        self,
        content: str,
        keywords: list[tuple[str, str, str]] | None = None,
    ) -> dict[str, Any]:
        """Scan content for risk keywords (deterministic).

        Args:
            content: Text to scan.
            keywords: Optional keyword list from the ``risk_keywords``
                table. When ``None`` (no-db path), the module-level
                hardcoded ``_RISKY_KEYWORDS`` catalog is used. When a
                list is passed (table-driven path), the db keywords are
                MERGED with the hardcoded catalog (db wins on duplicates)
                so the well-known spec-007 keywords — ``保本`` /
                ``100%`` / ``100% cure`` / ``guaranteed no loss`` — keep
                firing regardless of the seed coverage. The seed has no
                ``保本`` / ``100%`` / ``100% cure`` entries, so dropping
                the hardcoded list would regress T069 / T070 and
                acceptance scenario E.

        Returns:
            A dict shaped like ``{risks, overall_risk_score, confidence}``.
        """
        if keywords is None:
            kw_list = _RISKY_KEYWORDS
        else:
            # Merge: db keywords win on exact-text duplicates (so a
            # per-user override downgrading a hardcoded high -> low
            # still takes effect).
            seen: set[str] = set()
            kw_list: list[tuple[str, str, str]] = []
            for kw, severity, category in list(keywords) + list(_RISKY_KEYWORDS):
                if kw in seen:
                    continue
                seen.add(kw)
                kw_list.append((kw, severity, category))
        content_lower = content.lower()
        # (severity, category) -> set of keywords (for dedupe + description)
        bucket: dict[tuple[str, str], list[str]] = {}
        for kw, severity, category in kw_list:
            if kw.lower() in content_lower:
                bucket.setdefault((severity, category), []).append(kw)

        risks: list[dict[str, Any]] = []
        for (severity, category), kws in bucket.items():
            display_kw = kws[0]
            risks.append({
                "category": category,
                "description": f"内容包含{severity}风险关键词: {display_kw}",
                "severity": severity,
                "suggestion": f"建议替换或删除'{display_kw}'相关表述",
            })

        if not risks:
            overall = 0.1
        else:
            severity_scores = {"high": 0.8, "medium": 0.5, "low": 0.2}
            scores = [severity_scores.get(r["severity"], 0.3) for r in risks]
            overall = min(sum(scores) / len(scores) + 0.1, 1.0)

        confidence = round(1.0 - overall, 4)

        return {
            "risks": risks,
            "overall_risk_score": round(overall, 4),
            "confidence": confidence,
        }

    # ---------------- LLM enhance (defensive) ----------------

    def _try_llm_enhance(self, content: str) -> dict[str, Any] | None:
        """Optionally refine the keyword scan with an LLM.

        Any failure — instantiation, API, JSON parse, schema mismatch —
        logs a warning and returns ``None`` so the caller falls back to
        the keyword-only result. The caller is responsible for the
        80/20 blend.
        """
        try:
            from app.core.llm import LLMClient
        except Exception as e:
            logger.warning(f"risk: LLMClient unavailable: {e}")
            return None

        try:
            llm = LLMClient()
            prompt = (
                "你是一个内容合规审查助手。请对以下内容做风险审查，"
                "严格以 JSON 格式输出：{\"risks\":["
                "{\"category\":\"...\",\"description\":\"...\","
                "\"severity\":\"low|medium|high\",\"suggestion\":\"...\"}"
                "],\"overall_risk_score\":0.0~1.0}。\n\n内容："
                + content[:2000]
            )
            raw = llm.generate(prompt=prompt, temperature=0.1)
        except Exception as e:
            logger.warning(f"risk: LLM call failed: {e}")
            return None

        try:
            cleaned = raw.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start : end + 1]
            data = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"risk: LLM JSON parse failed: {e}")
            return None

        if not isinstance(data, dict) or "risks" not in data:
            logger.warning("risk: LLM response missing 'risks' field")
            return None
        if not isinstance(data["risks"], list):
            logger.warning("risk: LLM 'risks' is not a list")
            return None
        return data

    # ---------------- 80/20 blend (US5 T075) ----------------

    def _merge_risks(
        self, keyword_risks: list[dict[str, Any]], llm_risks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Union keyword + LLM risks, deduping by (severity, category)."""
        severity_rank = {"high": 3, "medium": 2, "low": 1}
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for r in list(keyword_risks) + list(llm_risks):
            if not isinstance(r, dict):
                continue
            sev = str(r.get("severity", "low"))
            cat = str(r.get("category", ""))
            key = (sev, cat)
            if key not in merged:
                merged[key] = {
                    "category": cat,
                    "description": str(r.get("description", "")),
                    "severity": sev,
                    "suggestion": str(r.get("suggestion", "")),
                }
        # Stable order: high first, then by category.
        return sorted(
            merged.values(),
            key=lambda r: (-severity_rank.get(r["severity"], 0), r["category"]),
        )

    # ---------------- public API ----------------

    async def check(self, user_id: str, content: str) -> dict[str, Any]:
        """Run the 80/20 blend (US5 T075) and return a report dict.

        When a ``db`` was injected at construction time, the keyword
        library is (lazily) loaded from the ``risk_keywords`` table on
        the first call; per-user overrides are applied for the supplied
        ``user_id``. Without a db, the hardcoded ``_RISKY_KEYWORDS``
        list is the fallback.

        Args:
            user_id: User ID.
            content: Content text to analyze.

        Returns:
            Dict with risk report and AI transparency metadata
            (confidence, data_source, model_version).
        """
        # T401-T405: lazy-load seed + fetch effective keyword set for user.
        if self.db is not None:
            await self._load_seed_if_needed()
            keywords = await self._fetch_keywords(user_id)
        else:
            keywords = None
        scan = self._scan_risk(content, keywords=keywords)
        keyword_confidence = scan["confidence"]

        # LLM gate: only when keyword confidence is below threshold.
        llm_data: dict[str, Any] | None = None
        if keyword_confidence < _LLM_CONFIDENCE_THRESHOLD:
            llm_data = self._try_llm_enhance(content)

        # ---- blend (US5 T075) ----
        if llm_data is not None:
            llm_risks = [
                r for r in llm_data.get("risks", [])
                if isinstance(r, dict)
                and r.get("severity") in ("low", "medium", "high")
                and r.get("category")
            ]
            llm_score = float(
                llm_data.get("overall_risk_score", scan["overall_risk_score"])
            )
            llm_score = max(0.0, min(1.0, llm_score))

            final_score = (
                _KEYWORD_BLEND_WEIGHT * scan["overall_risk_score"]
                + _LLM_BLEND_WEIGHT * llm_score
            )
            final_risks = self._merge_risks(scan["risks"], llm_risks)
            final_confidence = max(_LLM_CONFIDENCE, keyword_confidence)
            data_source = "llm_simulation"
            model_version = _LLM_MODEL_VERSION
        else:
            final_score = scan["overall_risk_score"]
            final_risks = scan["risks"]
            final_confidence = min(keyword_confidence, _KEYWORD_ONLY_CONFIDENCE_CAP)
            data_source = "keyword_only"
            model_version = _KEYWORD_MODEL_VERSION

        # 90-day content TTL (Constitution XIII)
        expires_at = (
            datetime.now(UTC) + timedelta(days=90)
        ).isoformat().replace("+00:00", "Z")

        return {
            "id": f"cr-{user_id}-{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "content_text": content[:5000],
            "content_text_expires_at": expires_at,
            "risks": final_risks,
            "overall_risk_score": round(max(0.0, min(1.0, final_score)), 4),
            "confidence": round(final_confidence, 4),
            "data_source": data_source,
            "model_version": model_version,
            "created_at": utc_now(),
        }
