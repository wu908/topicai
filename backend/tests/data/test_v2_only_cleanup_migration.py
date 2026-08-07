"""Upgrade coverage for dropping empty legacy business tables."""

import shutil
import sqlite3

from app.data.migrations.runner import DEFAULT_MIGRATIONS_DIR, apply

LEGACY_TABLES = {
    "topic_recommendations",
    "viral_analyses",
    "idea_boosters",
    "title_optimizations",
    "track_diagnoses",
    "feedback_records",
    "feedback_analyses",
    "effect_reviews",
    "content_risks",
    "publish_suggestions",
    "user_events",
    "llm_call_logs",
    "upgrade_signals",
    "assets",
    "asset_usages",
    "asset_tags",
    "asset_tag_links",
    "platform_accounts",
    "team_members",
    "risk_keywords",
    "platform_tokens",
    "user_feedback",
}

V2_SHARED_TABLES = {"materials", "material_usages"}
V2_PROFILE_COLUMNS = {
    "id",
    "user_id",
    "niche",
    "target_audience",
    "growth_goal",
    "content_pillars_json",
    "voice_traits_json",
    "avoid_traits_json",
    "evidence_refs_json",
    "confirmation_state",
    "confirmed_at",
    "version",
    "profile_attributes_json",
    "created_at",
    "updated_at",
}


def test_cleanup_drops_legacy_tables_and_preserves_v2_data(tmp_path):
    old_migrations = tmp_path / "old-migrations"
    old_migrations.mkdir()
    for source in DEFAULT_MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"):
        if source.name < "045_":
            shutil.copy2(source, old_migrations / source.name)

    db = tmp_path / "upgrade.db"
    apply(db, old_migrations)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO users (id,email,username,password_hash,ai_calls_reset_at,created_at) "
            "VALUES ('u1','u1@test.local','user-one','hash','','2026-08-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO content_projects "
            "(id,owner_user_id,title,status,primary_goal,target_audience,last_action_at,"
            "version,idempotency_key,created_at,updated_at) "
            "VALUES ('p1','u1','kept','preparing','stable_publish','readers','2026-08-01',"
            "1,'keep-project','2026-08-01','2026-08-01')"
        )
        conn.execute(
            "INSERT INTO creator_profiles "
            "(id,user_id,track,content_formats,production_complexity,content_depth,"
            "hotspot_preference,recommendation_mode,rubric_weights,niche,target_audience,"
            "content_pillars_json,profile_attributes_json,created_at,updated_at) "
            "VALUES ('cp1','u1','knowledge','[]','low','deep','low','evergreen_deep',"
            "'{}','v2-niche','v2-audience','[\"pillar\"]','{}','2026-08-01','2026-08-01')"
        )
        conn.execute(
            "INSERT INTO assets "
            "(id,owner_id,filename,mime_type,type,size,url,used_count,created_at,updated_at) "
            "VALUES ('a1','u1','evidence.pdf','application/pdf','document',1,'/materials',"
            "0,'2026-08-01','2026-08-01')"
        )
        conn.execute(
            "INSERT INTO assets "
            "(id,owner_id,filename,mime_type,type,size,url,used_count,created_at,updated_at) "
            "VALUES ('a2','u1','legacy-audio.mp3','audio/mpeg','audio',1,'/materials/audio',"
            "0,'2026-08-01','2026-08-01')"
        )
        conn.execute(
            "INSERT INTO asset_usages (id,asset_id,article_id,used_at) "
            "VALUES ('au1','a1','p1','2026-08-01')"
        )
        conn.commit()

    apply(db, DEFAULT_MIGRATIONS_DIR)

    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert not (LEGACY_TABLES & tables)
        assert V2_SHARED_TABLES <= tables
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert {
            row[1] for row in conn.execute("PRAGMA table_info(creator_profiles)")
        } == V2_PROFILE_COLUMNS
        assert conn.execute(
            "SELECT niche,target_audience FROM creator_profiles WHERE id='cp1'"
        ).fetchone() == ("v2-niche", "v2-audience")
        assert conn.execute("SELECT title FROM content_projects WHERE id='p1'").fetchone()[0] == "kept"
        assert conn.execute("SELECT name FROM materials WHERE id='a1'").fetchone()[0] == "evidence.pdf"
        assert conn.execute("SELECT kind FROM materials WHERE id='a2'").fetchone()[0] == "document"
        assert conn.execute(
            "SELECT project_id FROM material_usages WHERE id='au1'"
        ).fetchone()[0] == "p1"
