# TopicAI Handoff: Growth Onboarding History Profile Merged

## Outcome

Growth onboarding history/profile work is merged to `main`.

- PR: https://github.com/wu908/topicai/pull/28
- Merge commit: `a246c4f2549809c6aadaf1764127a97696a467ef`
- Feature commit represented on the remote branch: `b2211b29a26de838d41cf435dd72ef25cf24c2bc`
- Branch: `feature/growth-onboarding-history-profile`

The slice covers product-mode context/selection, manual/CSV/JSON history import, per-item validation, partial success, idempotency replay, cross-import deduplication, 90-day raw-content retention, and an evidence-backed correctable creator profile. The profile remains provisional below ten notes, records confidence/limitations/evidence, and excludes rejected attributes from the active profile.

## References

- Spec and acceptance criteria: `specs/008-content-project-mvp/spec.md` (US4)
- Tasks: `specs/008-content-project-mvp/tasks.md` (T075-T083)
- Data model/API contract: `specs/008-content-project-mvp/data-model.md`, `specs/008-content-project-mvp/contracts/api-v2.md`
- Migration: `backend/app/data/migrations/042_growth_onboarding.sql`
- Mode service/routes/contracts: `backend/app/services/onboarding_mode.py`, `backend/app/api/v2/onboarding.py`, `backend/app/models/v2/onboarding.py`
- Import/profile services: `backend/app/services/history_import.py`, `backend/app/services/creator_profile_v2.py`
- Frontend flow: `frontend/src/pages/GrowthOnboarding/GrowthOnboardingPage.tsx`

## Verification

- Backend CI: passed; local suite `864 passed`
- Frontend CI: passed; local suite `386 passed, 2 skipped`
- Frontend build and ESLint: passed
- Ruff and mypy: passed
- Migration replay/fresh/upgrade/recovery tests: passed

## Next Work

The next meaningful dependency is Spec-008 US5 opportunity generation. Add the downstream integration test proving that rejected profile attributes are absent from generated opportunities, then implement the first-party/evergreen opportunity source contract and its API/UI flow. The current branch only proves the exclusion at the active-profile boundary because the v2 opportunity generator is not yet implemented.

The migration also adds `timezone`, `weekly_publish_goal`, and `consent_json`; wire these fields into the later settings flow when US8 is implemented.

## Local State

The remote merge was completed through GitHub's Git Data API because `git push` over HTTPS timed out/reset. The local checkout may still point at the feature branch and local commit `48572a1`; verify `origin/main` before making further changes. Existing untracked handoff documents remain user-owned and were not included in PR #28.

## Suggested Skills

- `code-review` for the next branch review against `origin/main`
- `tdd` for US5 opportunity-source and rejected-attribute integration tests
- `ponytail:ponytail` to keep the next slice minimal and first-party-source focused
