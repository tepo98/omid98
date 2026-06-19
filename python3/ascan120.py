import socket
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import subprocess

# ===== SETTINGS =====
INPUT_FILE = "ips.txt"
PORTS = [443, 8443, 2053, 2083, 2087, 2096]
THREADS = 80
TIMEOUT = 1
TOP = 100
MAX_LATENCY = 250

# ===== COLORS =====
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
C = "\033[1;36m"
W = "\033[0m"

lock = threading.Lock()
results = []

# ===== LOAD IPS =====
def load_ips():
    ips = []
    with open(INPUT_FILE, "r") as f:
        for line in f:
            ip = line.strip()
            if ":" in ip:
                ip = ip.split(":")[0]
            if ip:
                ips.append(ip)
    return list(set(ips))

# ===== TEST PORT =====
def test_port(ip, port):
    try:
        s = socket.socket()
        s.settimeout(TIMEOUT)

        t1 = time.time()
        s.connect((ip, port))
        s.close()
        t2 = time.time()

        return int((t2 - t1) * 1000)
    except:
        return None

# ===== SCAN =====
def scan_ip(ip):
    lat = []

    for p in PORTS:
        ms = test_port(ip, p)
        if ms:
            lat.append(ms)

    if not lat:
        print(f"{R}[FAIL]{W} {ip}")
        return

    avg = sum(lat) // len(lat)
    jitter = max(lat) - min(lat)
    score = 1000 - avg - (jitter * 2)

    if avg <= MAX_LATENCY:
        with lock:
            results.append((score, avg, ip))
        print(f"{G}[OK]{W} {ip} {avg}ms score:{score}")
    else:
        print(f"{Y}[SLOW]{W} {ip} {avg}ms")

# ===== EXPORT + FIXED CLIPBOARD =====
def export():
    results.sort(reverse=True)

    clean = [x[2] for x in results[:TOP]]
    port = [f"{x[2]}:443" for x in results[:TOP]]

    with open("clean.txt", "w") as f:
        f.write("\n".join(clean))

    with open("port.txt", "w") as f:
        f.write("\n".join(port))

    print(f"\n{C}[+] Saved clean.txt + port.txt{W}")

    # ===== REAL TERMUX CLIPBOARD FIX =====
    try:
        subprocess.run(
            ["termux-clipboard-set"],
            input="\n".join(clean).encode()
        )
        print(f"{G}[+] CLEAN copied to clipboard{W}")
    except:
        print(f"{R}[!] Clipboard failed (clean){W}")

    try:
        subprocess.run(
            ["termux-clipboard-set"],
            input="\n".join(port).encode()
        )
        print(f"{G}[+] PORT copied to clipboard{W}")
    except:
        print(f"{R}[!] Clipboard failed (port){W}")

# ===== MAIN =====
def main():
    ips = load_ips()

    print(f"{C}Scanning {len(ips)} IPs...{W}\n")

    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        ex.map(scan_ip, ips)

    export()

    print(f"\n{G}[DONE] TOP RESULTS{W}\n")
    for s, ms, ip in results[:TOP]:
        print(f"{ip} | {ms}ms | score:{s}")

if __name__ == "__main__":
    main()
