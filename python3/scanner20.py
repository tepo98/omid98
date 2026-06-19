from flask import Flask, render_template_string, jsonify
import socket
import threading
import time
import sqlite3

app = Flask(__name__)

INPUT_FILE = "ips.txt"
PORT = 443
MAX_LATENCY = 250

# ===== COLORS (terminal) =====
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
C = "\033[1;36m"
W = "\033[0m"

results = []
logs = []
running = False

DB = "scan.db"

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            ip TEXT,
            latency INTEGER,
            score INTEGER,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_db(ip, latency, score):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO results (ip, latency, score) VALUES (?,?,?)",
              (ip, latency, score))
    conn.commit()
    conn.close()

# ---------------- LOAD ----------------
def load_ips():
    ips = []
    try:
        with open(INPUT_FILE) as f:
            for line in f:
                ip = line.strip()
                if ":" in ip:
                    ip = ip.split(":")[0]
                if ip:
                    ips.append(ip)
    except:
        pass
    return list(set(ips))

# ---------------- TEST ----------------
def test_ip(ip):
    global results, logs

    try:
        t1 = time.time()
        s = socket.socket()
        s.settimeout(1)
        s.connect((ip, PORT))
        s.close()
        ms1 = int((time.time() - t1) * 1000)

        t2 = time.time()
        s = socket.socket()
        s.settimeout(1)
        s.connect((ip, PORT))
        s.close()
        ms2 = int((time.time() - t2) * 1000)

        avg = (ms1 + ms2) // 2
        jitter = abs(ms1 - ms2)

        score = 100 - (avg // 4) - (jitter * 3)

        if avg <= MAX_LATENCY and score > 0:
            results.append((score, avg, ip))
            save_db(ip, avg, score)

            if score > 85:
                print(f"{G}[OK]{W} {ip} {avg}ms S:{score}")
            elif score > 70:
                print(f"{Y}[OK]{W} {ip} {avg}ms S:{score}")
            else:
                print(f"{C}[OK]{W} {ip} {avg}ms S:{score}")
        else:
            print(f"{R}[FAIL]{W} {ip}")

    except:
        print(f"{R}[FAIL]{W} {ip}")

# ---------------- SCAN ----------------
def start_scan():
    global running
    if running:
        return
    running = True

    ips = load_ips()

    def worker():
        for ip in ips:
            test_ip(ip)
            time.sleep(0.02)

    threading.Thread(target=worker).start()

# ---------------- WEB UI ----------------
HTML = """
<html>
<head>
<title>scanner20</title>
<style>
body{background:#000;color:#0f0;font-family:monospace}
button{padding:10px;background:#111;color:#0f0;border:1px solid #0f0}
.box{border:1px solid #0f0;margin:10px;padding:10px}
</style>
</head>
<body>

<h2>⚡ scanner20 GOD PANEL</h2>

<form method="post">
<button name="start">START SCAN</button>
</form>

<div class="box">
<h3>TOP RESULTS</h3>
<pre>
{% for r in top %}
{{r}}
{% endfor %}
</pre>
</div>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    if "start" in str(app):
        pass

    top_sorted = sorted(results, reverse=True)[:20]
    formatted = [f"{ip} | {ms}ms | S:{score}" for score, ms, ip in top_sorted]

    return render_template_string(HTML, top=formatted)

# ---------------- API ----------------
@app.route("/api")
def api():
    top_sorted = sorted(results, reverse=True)[:20]
    return jsonify([
        {"ip": ip, "latency": ms, "score": score}
        for score, ms, ip in top_sorted
    ])

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    print(f"{C}scanner20 starting...{W}")
    start_scan()
    app.run(host="127.0.0.1", port=5000)
