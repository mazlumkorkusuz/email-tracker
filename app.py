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
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
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
    
    return send_file(io.BytesIO(PIXEL), mimetype='image/gif')

@app.route('/stats')
def stats():
    conn = sqlite3.connect('tracking.db')
    c = conn.cursor()
    c.execute('SELECT name, email, opened_at FROM opens ORDER BY opened_at DESC')
    rows = c.fetchall()
    conn.close()
    
    html = '''
    <html>
    <head>
        <title>Email Tracker</title>
        <style>
            body { font-family: Arial; background: #0d1527; color: #c8d8ec; padding: 20px; }
            h1 { color: #F0C040; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th { background: #111e3a; color: #F0C040; padding: 10px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #1e2d4a; }
            .count { font-size: 24px; color: #F0C040; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>📊 Email Tracking Dashboard</h1>
        <p>Toplam açılma: <span class="count">''' + str(len(rows)) + '''</span></p>
        <table>
            <tr><th>İsim</th><th>Email</th><th>Açılma Zamanı</th></tr>
    '''
    
    for row in rows:
        html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>'
    
    html += '</table></body></html>'
    return html

@app.route('/')
def home():
    return 'Email Tracker is running!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
