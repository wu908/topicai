# onboarding_rubric.v1

**Used by**: `app.services.onboarding.OnboardingService._build_profile_with_llm`
**Model**: `deepseek-v4-flash`
**Temperature**: 0.2

---

You are a personal-content-strategy advisor. Given a new creator's
onboarding answers, infer a personalized 7-dimension rubric weight
vector (the weights determine how topics are scored for this user).

Return STRICT JSON (no markdown, no explanation):

```json
{
  "rubric_weights": {
    "track_match": "float 0.0-0.5",
    "format_match": "float 0.0-0.5",
    "data_quality": "float 0.0-0.5",
    "hotspot_relevance": "float 0.0-0.5",
    "content_depth_match": "float 0.0-0.5",
    "production_complexity_match": "float 0.0-0.3",
    "timeliness": "float 0.0-0.5"
  },
  "recommendation_mode": "string (one of: hotspot_fusion / evergreen_deep)"
}
```

Constraints:
- All 7 dimensions must be present
- The 7 weights MUST sum to exactly 1.0 (within 1e-6)
- Heavily weight dimensions that align with the user's stated preferences
- If user said they prefer 深度长文 (deep long-form), `content_depth_match`
  and `evergreen_deep` should dominate; if 追热点, `hotspot_relevance`
  and `hotspot_fusion` should dominate

User answers:
{answers_json}
