import sqlite3
c = sqlite3.connect('/app/data/topicai.db')
n = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
print('USER_COUNT', n)
emails = [r[0] for r in c.execute('SELECT email FROM users ORDER BY email')]
print('EMAILS', emails)
c.close()
