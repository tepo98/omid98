import socket
import time
import os
from concurrent.futures import ThreadPoolExecutor

# ===== COLORS =====
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
C = "\033[1;36m"
W = "\033[0m"

INPUT_FILE = "ips.txt"

PORT = 443
THREADS = 120
TOP = 20
MAX_LATENCY = 250

results = []
seen = set()

# ---------- load ----------
def load_ips():
    ips = []
    with open(INPUT_FILE, "r") as f:
        for line in f:
            ip = line.strip()
            if ":" in ip:
                ip = ip.split(":")[0]
            if ip and ip not in seen:
                seen.add(ip)
                ips.append(ip)
    return ips

# ---------- test ----------
def test_ip(ip):
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

            if score > 85:
                color = G
            elif score > 70:
                color = Y
            else:
                color = C

            print(f"{color}[OK]{W} {ip} | {avg}ms | S:{score}")

    except:
        print(f"{R}[FAIL]{W} {ip}")

# ---------- UI ----------
def banner():
    os.system("clear")
    print(f"{C}=================================={W}")
    print(f"{G}      GOD PANEL IP SCANNER       {W}")
    print(f"{C}=================================={W}")
    print()

def menu():
    print(f"{Y}[1]{W} START SCAN")
    print(f"{Y}[2]{W} EXIT")
    print()

# ---------- scan ----------
def start_scan():
    ips = load_ips()

    print(f"\n{C}[*] SCANNING STARTED...{W}\n")

    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        ex.map(test_ip, ips)

    results.sort(reverse=True)

    top = results[:TOP]
    clean = [x[2] for x in top]

    with open("clean.txt", "w") as f:
        f.write("\n".join(clean))

    with open("port.txt", "w") as f:
        for ip in clean:
            f.write(f"{ip}:{PORT}\n")

    print(f"\n{G}===== TOP IPS ====={W}")
    for s, ms, ip in top:
        print(f"{ip} | {ms}ms | S:{s}")

    os.system("cat clean.txt port.txt | termux-clipboard-set")

    print(f"\n{G}[✓] COPIED TO CLIPBOARD{W}")
    input("\nPress Enter...")

# ---------- main ----------
def main():
    while True:
        banner()
        menu()
        c = input("Select: ")

        if c == "1":
            start_scan()
        elif c == "2":
            break

if __name__ == "__main__":
    main()
