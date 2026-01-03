from flask import Flask, render_template_string, request
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import threading
import time
import os
import math

app = Flask(__name__)

# ======================
# SQLITE
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tongsampah.db")

# ======================
# FIREBASE (LOCAL FILE)
# ======================
import json

firebase_key = json.loads(os.environ["FIREBASE_KEY"])
cred = credentials.Certificate(firebase_key)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tongsampah-fb84c-default-rtdb.firebaseio.com/"
})

# ======================
# INIT DB
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS data_tongsampah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tong_id INTEGER,
            organik INTEGER,
            anorganik INTEGER,
            b3 INTEGER,
            timestamp INTEGER,
            waktu TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ======================
# MAP TONG
# ======================
TONG_MAP = {
    "Tongsampah1": 1,
    "Tongsampah2": 2,
    "Tongsampah3": 3
}

# ======================
# % → INT
# ======================
def persen_ke_int(val):
    try:
        return int(str(val).replace("%", "").strip())
    except:
        return 0

# ======================
# SIMPAN
# ======================
def simpan_ke_db(tong_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO data_tongsampah
        (tong_id, organik, anorganik, b3, timestamp, waktu)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        tong_id,
        persen_ke_int(data.get("organik")),
        persen_ke_int(data.get("anorganik")),
        persen_ke_int(data.get("b3")),
        data.get("timestamp"),
        data.get("waktu")
    ))

    conn.commit()
    conn.close()
    print(f"✅ LOG MASUK | Tong {tong_id}")

# ======================
# LOGGER 1 MENIT
# ======================
def logger_1_menit():
    print("🚀 LOGGER AKTIF (1 MENIT)")
    while True:
        for tong, tid in TONG_MAP.items():
            data = db.reference(tong).get()
            if data:
                simpan_ke_db(tid, data)
        time.sleep(60)

# ======================
# DASHBOARD
# ======================
@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM data_tongsampah")
    total = c.fetchone()[0]
    total_pages = max(1, math.ceil(total / per_page))

    c.execute("""
        SELECT * FROM data_tongsampah
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    rows = c.fetchall()
    conn.close()

    return render_template_string("""
    <html>
    <head>
        <title>Log Tongsampah</title>
        <style>
            body { background:#f1f8f4; font-family:Arial; }
            .card { width:90%; max-width:1100px; margin:40px auto;
                    background:white; padding:20px;
                    border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,.1); }
            table { width:100%; border-collapse:collapse; }
            th { background:#2e7d32; color:white; padding:10px; }
            td { text-align:center; padding:8px; }
            tr:nth-child(even){ background:#e8f5e9; }
        </style>
        <script>
            setTimeout(()=>location.reload(),5000);
        </script>
    </head>
    <body>
        <div class="card">
        <h2 align="center">LOG HISTORY TONG SAMPAH</h2>
        <table>
            <tr>
                <th>ID</th><th>Tong</th><th>Organik</th>
                <th>Anorganik</th><th>B3</th><th>Timestamp</th><th>Waktu</th>
            </tr>
            {% for r in rows %}
            <tr>
                <td>{{r.id}}</td>
                <td>{{r.tong_id}}</td>
                <td>{{r.organik}}%</td>
                <td>{{r.anorganik}}%</td>
                <td>{{r.b3}}%</td>
                <td>{{r.timestamp}}</td>
                <td>{{r.waktu}}</td>
            </tr>
            {% endfor %}
        </table>
        </div>
    </body>
    </html>
    """, rows=rows)

# ======================
# RUN
# ======================
if __name__ == "__main__":
    threading.Thread(target=logger_1_menit, daemon=True).start()
    app.run(debug=True)
