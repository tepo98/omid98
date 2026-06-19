#!/data/data/com.termux/files/usr/bin/bash

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
NC="\033[0m"

INPUT="ips.txt"

TMP="tmp.db"
CLEAN="clean.txt"
PORT_OUT="port.txt"
HISTORY="history.txt"

PORT=443
TOP=100
THREADS=30
MAX_LATENCY=150

banner() {
clear
echo -e "${CYAN}"
echo "█████████████████████████████"
echo "   BLACK UI IP SCANNER PRO"
echo "█████████████████████████████"
echo -e "${NC}"
}

scan_ip() {
    ip=$1

    res=$(ping -c 1 -W 1 $ip 2>/dev/null | grep "time=")

    if [ $? -eq 0 ]; then
        t=$(echo $res | sed 's/.*time=//' | cut -d' ' -f1)

        cmp=$(echo "$t < $MAX_LATENCY" | bc)

        if [ "$cmp" -eq 1 ]; then
            echo -e "${GREEN}[OK] $ip ${YELLOW}${t}ms${NC}"
            echo "$t $ip" >> "$TMP"
        fi
    else
        echo -e "${RED}[FAIL] $ip${NC}"
    fi
}

start_scan() {

    > "$TMP"
    > "$CLEAN"
    > "$PORT_OUT"

    echo -e "${CYAN}[*] Scanning...${NC}"

    i=0
    while read ip; do
        ((i=i%THREADS)); ((i++==0)) && wait
        scan_ip "$ip" &
    done < "$INPUT"

    wait

    sort -n "$TMP" | awk '{print $2}' | head -n $TOP > "$CLEAN"

    while read ip; do
        echo "$ip:$PORT" >> "$PORT_OUT"
    done < "$CLEAN"

    cat "$CLEAN" >> "$HISTORY"

    echo -e "${GREEN}\nTOP CLEAN:${NC}"
    cat "$CLEAN"

    echo -e "${YELLOW}\nTOP PORT:${NC}"
    cat "$PORT_OUT"

    cat "$CLEAN" | termux-clipboard-set
    echo -e "${GREEN}[+] Copied CLEAN${NC}"

    sleep 1
    cat "$PORT_OUT" | termux-clipboard-set
    echo -e "${GREEN}[+] Copied PORT${NC}"
}

auto_scan() {
    while true; do
        banner
        echo -e "${YELLOW}AUTO MODE ACTIVE... CTRL+C to stop${NC}"
        start_scan
        sleep 10
    done
}

menu() {
while true; do
    banner
    echo "1) START SCAN"
    echo "2) AUTO SCAN"
    echo "3) SET TOP ($TOP)"
    echo "4) SET LATENCY ($MAX_LATENCY)"
    echo "5) SET PORT ($PORT)"
    echo "6) EXIT"
    echo
    read -p "SELECT: " c

    case $c in
        1) start_scan; read -p "ENTER..." ;;
        2) auto_scan ;;
        3) read -p "TOP: " TOP ;;
        4) read -p "LATENCY: " MAX_LATENCY ;;
        5) read -p "PORT: " PORT ;;
        6) exit 0 ;;
    esac
done
}

menu
