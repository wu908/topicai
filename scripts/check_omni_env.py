import os
k = os.environ.get("OMNI_API_KEY", "")
print("ENABLED", os.environ.get("OMNI_ENABLED"))
print("MODEL", os.environ.get("OMNI_MODEL"))
print("BASE", os.environ.get("OMNI_BASE_URL"))
print("KEY_LEN", len(k), "PREFIX_OK", k.startswith("sk-"))
print("TIMEOUT", os.environ.get("OMNI_TIMEOUT_SECONDS"))
print("MAX_BYTES", os.environ.get("OMNI_MAX_MEDIA_BYTES"))
