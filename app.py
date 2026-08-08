from flask import Flask, request, send_file, jsonify
import sqlite3
import io
import base64
import datetime
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('tracking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS opens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT,
                  name TEXT,
                  opened_at TEXT,
                  ip TEXT,
                  user_agent TEXT)''')
    conn.commit()
    conn.close()

init_db()

PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)

@app.route('/track')
def track():
    email = request.args.get('e', '')
    name = request.args.get('n', '')
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('tracking.db')
    c = conn.cursor()
    c.execute('INSERT INTO opens (email, name, opened_at, ip, user_agent) VALUES (?, ?, ?, ?, ?)',
              (email, name, now, ip, ua))
    conn.commit()
    conn.close()
    
    return send_file(io.BytesIO(PIXEL), mimetype='image/png')

@app.route('/stats')
def stats():
    conn = sqlite3.connect('tracking.db')
    c = conn.cursor()
    
    # Toplam açılma
    c.execute('SELECT COUNT(*) FROM opens')
    total = c.fetchone()[0]
    
    # Unique kişi sayısı
    c.execute('SELECT COUNT(DISTINCT LOWER(email)) FROM opens WHERE email != ""')
    unique = c.fetchone()[0]
    
    # Unique kişiler listesi (son açılma zamanıyla)
    c.execute('''SELECT name, email, COUNT(*) as kez, MAX(opened_at) as son_acilis 
                 FROM opens 
                 WHERE email != ""
                 GROUP BY LOWER(email) 
                 ORDER BY son_acilis DESC''')
    rows = c.fetchall()
    conn.close()
    
    html = '''
    <html>
    <head>
        <title>Email Tracker</title>
        <style>
            body { font-family: Arial; background: #0d1527; color: #c8d8ec; padding: 20px; }
            h1 { color: #F0C040; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat-box { background: #111e3a; border: 1px solid #8B6914; border-radius: 4px; padding: 16px 24px; text-align: center; }
            .stat-number { font-size: 32px; color: #F0C040; font-weight: bold; }
            .stat-label { font-size: 12px; color: #8fa8c8; margin-top: 4px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #111e3a; color: #F0C040; padding: 10px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #1e2d4a; }
            .badge { background: #8B6914; color: #fff; border-radius: 10px; padding: 2px 8px; font-size: 11px; }
        </style>
    </head>
    <body>
        <h1>📊 Email Tracking Dashboard</h1>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">''' + str(total) + '''</div>
                <div class="stat-label">Toplam Açılma</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">''' + str(unique) + '''</div>
                <div class="stat-label">Unique Kişi</div>
            </div>
        </div>
        <table>
            <tr><th>İsim</th><th>Email</th><th>Kaç Kez Açtı</th><th>Son Açılma</th></tr>
    '''
    
    for row in rows:
        kez = row[2]
        badge = f'<span class="badge">{kez}x</span>' if kez > 1 else ''
        html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{badge} {kez}</td><td>{row[3]}</td></tr>'
    
    html += '</table></body></html>'
    return html

@app.route('/')
def home():
    return 'Email Tracker is running!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
