#!/bin/bash
set -euo pipefail
MID="$1"
OWNER="$2"
docker exec -i topicai-backend env PYTHONPATH=/app python - <<PY
import sqlite3, os
url = os.environ.get('DATABASE_URL') or 'sqlite+aiosqlite:////app/data/topicai.db'
path = url.split('///')[-1]
print('USING', path)
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
cols = [r[1] for r in conn.execute('PRAGMA table_info(materials)')]
print('MATERIAL_COLS', cols)
mat = conn.execute(
    'SELECT id,name,kind,mime_type,size,content_text,analysis_json,privacy_level FROM materials WHERE id=?',
    ('$MID',)
).fetchone()
print('MATERIAL_ROW', dict(mat) if mat else None)
if mat and mat['analysis_json']:
    print('ANALYSIS_JSON', mat['analysis_json'])
traces = conn.execute(
    'SELECT id,task_type,capability,model_identifier,outcome,actual_json,generated_at '
    'FROM ai_traces_v2 WHERE owner_user_id=? ORDER BY generated_at DESC LIMIT 8',
    ('$OWNER',)
).fetchall()
for t in traces:
    row = dict(t)
    actual = row.get('actual_json') or ''
    print('TRACE', row.get('task_type'), row.get('capability'), row.get('model_identifier'),
          row.get('outcome'), 'has_external_model_read=', 'external_model_read' in actual)
    print('TRACE_ACTUAL', actual[:500])
conn.close()
PY
