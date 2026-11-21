import os
import random
import time
from typing import List

from config import (
    PRIVATE_KEYS_FILE,
    PROXIES_FILE,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS
)
from src.bot import CoConnectBot
from src.logger import (
    print_banner,
    print_config_box,
    log_info,
    log_warning,
    log_error,
    print_summary_table
)

def load_lines(filepath: str) -> List[str]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def run_daily_cycle():
    print_banner()
    start_time = time.time()
    log_info("Memulai Siklus Harian (Daily Streak & Spin Auto-Claim)...")
    
    keys = load_lines(PRIVATE_KEYS_FILE)
    if not keys:
        log_warning(f"File '{PRIVATE_KEYS_FILE}' kosong atau tidak ditemukan.")
        return

    proxies = load_lines(PROXIES_FILE)
    print_config_box(
        total_wallets=len(keys),
        min_delay=MIN_DELAY_SECONDS,
        max_delay=MAX_DELAY_SECONDS,
        proxy_count=len(proxies)
    )
    results = []

    for idx, pk in enumerate(keys, 1):
        proxy = proxies[(idx - 1) % len(proxies)] if proxies else None

        try:
            bot = CoConnectBot(private_key=pk, proxy=proxy)
            res = bot.run(wallet_num=idx, total_wallets=len(keys))
            results.append(res)
        except Exception as e:
            log_error(f"Error pada wallet #{idx}: {e}")
            results.append({
                "address": f"Key #{idx}",
                "handle": "-",
                "checkin_status": "Error",
                "spin_status": "Error",
                "tasks_done": 0,
                "badges_count": 0,
                "loot_box_status": "-",
                "streak": 0,
                "total_xp": 0,
                "status": "ERROR"
            })

        if idx < len(keys):
            delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            log_info(f"Jeda anti-sybil {delay:.1f}s sebelum akun berikutnya...")
            time.sleep(delay)

    elapsed = time.time() - start_time
    print_summary_table(results, elapsed_seconds=elapsed)

if __name__ == "__main__":
    run_daily_cycle()
