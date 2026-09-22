#!/bin/bash
# merge OMNI_* from /tmp/omni.env.local into /opt/topicai/.env; never print key values
set -euo pipefail

SRC=/tmp/omni.env.local
DST=/opt/topicai/.env
[ -f "$SRC" ] || { echo "MISSING_SRC"; exit 1; }
[ -f "$DST" ] || { echo "MISSING_DST"; exit 1; }

BAK="${DST}.bak-before-omni-$(date +%Y%m%d-%H%M%S)"
cp "$DST" "$BAK"
echo "BACKUP $BAK"

for k in OMNI_ENABLED OMNI_BASE_URL OMNI_API_KEY OMNI_MODEL OMNI_TIMEOUT_SECONDS OMNI_MAX_MEDIA_BYTES; do
  v=$(grep -E "^${k}=" "$SRC" | head -1 | cut -d= -f2-)
  if grep -qE "^${k}=" "$DST"; then
    KEY="$k" VAL="$v" python3 - <<'PY'
import os
from pathlib import Path
p = Path('/opt/topicai/.env')
key = os.environ['KEY']
val = os.environ['VAL']
out = []
replaced = False
for line in p.read_text().splitlines(True):
    if line.startswith(key + '=') and not replaced:
        out.append(key + '=' + val + '\n')
        replaced = True
    else:
        out.append(line)
if not replaced:
    out.append(key + '=' + val + '\n')
p.write_text(''.join(out))
print('updated', key, 'value_len', len(val))
PY
  else
    printf '%s=%s\n' "$k" "$v" >> "$DST"
    echo "appended $k value_len ${#v}"
  fi
done

echo "--- OMNI names only ---"
grep -E '^OMNI_' "$DST" | sed 's/=.*$/=<set>/'

python3 - <<'PY'
from pathlib import Path
vals = {}
for line in Path('/opt/topicai/.env').read_text().splitlines():
    if line.startswith('OMNI_') and '=' in line:
        k, v = line.split('=', 1)
        vals[k] = v
assert vals.get('OMNI_ENABLED') == 'true', 'OMNI_ENABLED not true'
assert vals.get('OMNI_API_KEY', '').startswith('sk-'), 'key missing or bad prefix'
assert vals.get('OMNI_MODEL') == 'mimo-v2.6-flash', 'model wrong: %r' % vals.get('OMNI_MODEL')
assert vals.get('OMNI_BASE_URL', '').startswith('https://api.xiaomimimo.com'), 'base_url wrong'
print('ENV_VALIDATED key_len=', len(vals.get('OMNI_API_KEY', '')), 'model=', vals.get('OMNI_MODEL'))
PY

rm -f "$SRC"
echo "SRC_REMOVED"
