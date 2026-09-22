import sqlite3
c = sqlite3.connect('/app/data/topicai.db')
c.row_factory = sqlite3.Row
print('TRACE_COLS', [r[1] for r in c.execute('PRAGMA table_info(ai_traces_v2)')])
rows = c.execute(
    'SELECT * FROM ai_traces_v2 WHERE owner_user_id=? ORDER BY generated_at DESC LIMIT 5',
    ('5fc4ace4-f2b4-43d6-80f6-89d534d8e82f',)
).fetchall()
for row in rows:
    d = dict(row)
    print('TRACE_KEYS', sorted(d.keys()))
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 200:
            v = v[:200] + '...'
        print(' ', k, '=', v)
c.close()
