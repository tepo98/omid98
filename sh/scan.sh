#!/data/data/com.termux/files/usr/bin/bash

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
NC="\033[0m"

INPUT="ips.txt"

TMP="tmp.db"
SCORED="scored.db"

ELITE="elite.txt"
FAST="fast.txt"
OK="ok.txt"
WEAK="weak.txt"

CLEAN="clean.txt"
PORT_OUT="port.txt"

PORT=443
THREADS=80
TOP=50
MAX_LATENCY=450

banner() {
clear
echo -e "${CYAN}"
echo "=================================="
echo "   ULTIMATE MACHINE AI ENGINE"
echo "=================================="
echo -e "${NC}"
}

test_ip() {
    ip=$1

    # TCP test
    t1=$(date +%s%N)
    timeout 1 bash -c "echo > /dev/tcp/$ip/$PORT" 2>/dev/null
    if [ $? -ne 0 ]; then
        return
    fi
    t2=$(date +%s%N)

    ms=$(( (t2 - t1) / 1000000 ))

    # jitter
    t3=$(date +%s%N)
    timeout 1 bash -c "echo > /dev/tcp/$ip/$PORT" 2>/dev/null
    t4=$(date +%s%N)

    ms2=$(( (t4 - t3) / 1000000 ))
    jitter=$(( ms > ms2 ? ms - ms2 : ms2 - ms ))

    # stability score
    stability=$((100 - (jitter*2)))
    [ "$stability" -lt 0 ] && stability=0

    # base AI score
    score=$((100 - (ms/5) - (jitter*3) + (stability/6)))

    # penalties
    [ "$ms" -gt 200 ] && score=$((score-10))
    [ "$ms" -gt 300 ] && score=$((score-20))
    [ "$ms" -gt 400 ] && score=$((score-30))

    [ "$score" -lt 0 ] && score=0

    if [ "$ms" -lt "$MAX_LATENCY" ]; then
        echo "$score $ms $ip" >> "$SCORED"
    fi
}

dedup() {
    sort -u "$1" -o "$1"
}

start_scan() {

    > "$SCORED"
    > "$ELITE"
    > "$FAST"
    > "$OK"
    > "$WEAK"
    > "$CLEAN"
    > "$PORT_OUT"

    dedup "$INPUT"

    echo -e "${CYAN}[*] ULTIMATE AI SCAN STARTED...${NC}"

    i=0
    while read ip; do
        ((i=i%THREADS)); ((i++==0)) && wait
        test_ip "$ip" &
    done < "$INPUT"

    wait

    echo -e "${YELLOW}\n[*] Ranking & clustering...${NC}"

    sort -nr "$SCORED" | while read score ms ip; do

        if [ "$score" -ge 85 ]; then
            echo "$ip" >> "$ELITE"
        elif [ "$score" -ge 70 ]; then
            echo "$ip" >> "$FAST"
        elif [ "$score" -ge 50 ]; then
            echo "$ip" >> "$OK"
        else
            echo "$ip" >> "$WEAK"
        fi

    done

    cat "$ELITE" "$FAST" "$OK" | head -n "$TOP" > "$CLEAN"

    while read ip; do
        echo "$ip:$PORT" >> "$PORT_OUT"
    done < "$CLEAN"

    echo -e "${GREEN}\n===== ELITE =====${NC}"
    cat "$ELITE"

    echo -e "${GREEN}\n===== FAST =====${NC}"
    cat "$FAST"

    echo -e "${YELLOW}\n===== OK =====${NC}"
    cat "$OK"

    echo -e "${RED}\n===== WEAK =====${NC}"
    cat "$WEAK"

    echo -e "${CYAN}\n===== FINAL CLEAN TOP =====${NC}"
    cat "$CLEAN"

    echo -e "${YELLOW}\n===== PORT OUTPUT =====${NC}"
    cat "$PORT_OUT"

    cat "$CLEAN" "$PORT_OUT" | termux-clipboard-set

    echo ""
    echo "[✓] COPIED TO CLIPBOARD"
    echo "[✓] ULTIMATE MODE DONE"
}

auto_loop() {
    while true; do
        start_scan
        sleep 10
    done
}

menu() {
while true; do
    banner
    echo "1) START ULTIMATE SCAN"
    echo "2) AUTO LOOP MODE"
    echo "3) EXIT"
    echo
    read -p "SELECT: " c

    case $c in
        1) start_scan; read -p "ENTER..." ;;
        2) auto_loop ;;
        3) exit 0 ;;
    esac
done
}

menu
