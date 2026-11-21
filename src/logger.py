import ctypes
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import wcwidth

# ============================================================================
# 1. WINDOWS CONSOLE UTF-8 & VIRTUAL TERMINAL MODE INITIALIZATION
# ============================================================================
if sys.platform == "win32":
    try:
        kernel32 = ctypes.windll.kernel32
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004, ENABLE_PROCESSED_OUTPUT = 0x0001, ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ============================================================================
# 2. HIGH-DEFINITION ANSI PALETTE & PRECISION STRING PADDING UTILS
# ============================================================================
CYAN = '\033[36m'
BRIGHT_CYAN = '\033[96m'
GREEN = '\033[32m'
BRIGHT_GREEN = '\033[92m'
YELLOW = '\033[33m'
BRIGHT_YELLOW = '\033[93m'
MAGENTA = '\033[35m'
BRIGHT_MAGENTA = '\033[95m'
RED = '\033[31m'
BRIGHT_RED = '\033[91m'
WHITE = '\033[37m'
BRIGHT_WHITE = '\033[97m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s: str) -> str:
    """Menghapus kode ANSI escape untuk perhitungan panjang string murni."""
    return ANSI_REGEX.sub('', str(s))

def vlen(s: str) -> int:
    """Menghitung lebar kolom visual terminal murni dengan wcwidth (akurat untuk emoji & CJK)."""
    plain = strip_ansi(str(s))
    w = wcwidth.wcswidth(plain)
    return w if w >= 0 else len(plain)

def pad(text: str, width: int, align: str = 'left') -> str:
    """Pad string ke lebar visual presisi tanpa mengabaikan kode warna ANSI."""
    diff = max(0, width - vlen(text))
    if align == 'right':
        return (' ' * diff) + str(text)
    elif align == 'center':
        left = diff // 2
        right = diff - left
        return (' ' * left) + str(text) + (' ' * right)
    return str(text) + (' ' * diff)

def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")

# ============================================================================
# 3. UNIFIED GLOBAL WIDTH & CARD FRAMING
# ============================================================================
TABLE_COLS = [
    ("No", 3, "center"),
    ("Address", 13, "center"),
    ("Username", 16, "left"),
    ("Check-In", 14, "center"),
    ("Spin Wheel", 14, "center"),
    ("Streak", 6, "center"),
    ("Badges", 8, "center"),
    ("Total XP", 8, "right"),
    ("Status", 6, "center"),
]

# Total unified width across all UI blocks: 88 (content) + 18 (padding) + 10 (borders) = 116
BOX_WIDTH = sum(w + 3 for _, w, _ in TABLE_COLS) + 1

def pad_box(content: str, width: int = BOX_WIDTH, border_col: str = CYAN) -> str:
    inner = width - 4
    diff = max(0, inner - vlen(content))
    return f"{border_col}│{RESET}  {content}{' ' * diff}{border_col}│{RESET}"

def pad_box_center(content: str, width: int = BOX_WIDTH, border_col: str = CYAN) -> str:
    inner = width - 2
    return f"{border_col}│{RESET}{pad(content, inner, 'center')}{border_col}│{RESET}"

def make_box_top(title: str = "", width: int = BOX_WIDTH, border_col: str = CYAN) -> str:
    if not title:
        return f"{border_col}┌{'─' * (width - 2)}┐{RESET}"
    dash_r = max(0, width - 2 - vlen(title) - 4)
    return f"{border_col}┌── {BOLD}{BRIGHT_WHITE}{title}{RESET} {border_col}{'─' * dash_r}┐{RESET}"

def make_box_bottom(width: int = BOX_WIDTH, border_col: str = CYAN) -> str:
    return f"{border_col}└{'─' * (width - 2)}┘{RESET}"

def make_sep(left: str, mid: str, right: str, char: str = '─') -> str:
    parts = [char * (w + 2) for _, w, _ in TABLE_COLS]
    return f"{CYAN}{left}{mid.join(parts)}{right}{RESET}"

# ============================================================================
# 4. BANNER & CONFIGURATION PANEL
# ============================================================================
def print_banner():
    banner_art = f"""{BRIGHT_CYAN}
   ____ ___   ____ ___  _   _ _   _ _____ ____ _____ 
  / ___/ _ \ / ___/ _ \| \ | | \ | | ____/ ___|_   _|
 | |  | | | | |  | | | |  \| |  \| |  _| | |     | |  
 | |__| |_| | |__| |_| | |\  | |\  | |___| |___  | |  
  \____\___/ \____\___/|_| \_|_| \_|_____|\____| |_|  {RESET}"""
    print(banner_art)
    print(make_box_top(width=BOX_WIDTH))
    print(pad_box_center(f"{BOLD}{BRIGHT_YELLOW}⚡ COCONNECT HUB AIRDROP AUTOMATION SUITE · MULTI-WALLET EVM SIWE ⚡{RESET}"))
    print(pad_box_center(f"{DIM}{WHITE}Reward Pool: 5,000 USDC & Points │ Auto SIWE · Daily Streak · Badges · Free Loot Boxes{RESET}"))
    print(make_box_bottom(width=BOX_WIDTH))
    print()

def print_config_box(total_wallets: int, min_delay: float, max_delay: float, proxy_count: int):
    proxy_str = f"{BRIGHT_GREEN}{proxy_count} Multi-Proxy Aktif{RESET}" if proxy_count > 0 else f"{BRIGHT_YELLOW}Direct (Tanpa Proxy){RESET}"
    print(make_box_top("[ KONFIGURASI SISTEM & JARINGAN ]", width=BOX_WIDTH))
    print(pad_box(f"{BOLD}{WHITE}Target Platform   :{RESET} {BRIGHT_CYAN}CoConnect Hub (https://hub.coconnect.co){RESET}"))
    print(pad_box(f"{BOLD}{WHITE}Total EVM Wallets :{RESET} {BOLD}{BRIGHT_GREEN}{total_wallets} Akun Terdaftar{RESET}{' ' * 4}│  {BOLD}{WHITE}Status Jaringan :{RESET} {proxy_str}"))
    print(pad_box(f"{BOLD}{WHITE}Anti-Sybil Jitter :{RESET} {BRIGHT_YELLOW}{min_delay}s - {max_delay}s Detik{RESET}{' ' * 10}│  {BOLD}{WHITE}Otentikasi      :{RESET} {BRIGHT_CYAN}EIP-4361 SIWE Sign-In{RESET}"))
    print(make_box_bottom(width=BOX_WIDTH))
    print()

# ============================================================================
# 5. RUNTIME LOGGING & WALLET ENCLOSED CARDS
# ============================================================================
def log_wallet_header(wallet_num: int, total_wallets: int, address: str, handle: str = ""):
    handle_str = f" (@{handle})" if handle and handle != "-" else ""
    title = f"[ AKUN {wallet_num:02d}/{total_wallets:02d} ] {address}{handle_str}"
    print(make_box_top(title, width=BOX_WIDTH))

def log_auth(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_CYAN}➜ [AUTH    ]{RESET} {msg}"
    print(pad_box(content))

def log_profile(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_MAGENTA}➜ [PROFILE ]{RESET} {msg}"
    print(pad_box(content))

def log_checkin(msg: str, status: str = "ok"):
    if status == "ok":
        tag = f"{BRIGHT_GREEN}➜ [CHECKIN ]{RESET}"
        text = f"{BRIGHT_GREEN}{msg}{RESET}"
    else:
        tag = f"{BRIGHT_YELLOW}➜ [CHECKIN ]{RESET}"
        text = f"{BRIGHT_YELLOW}{msg}{RESET}"
    content = f"{DIM}[{_timestamp()}]{RESET}   {tag} {text}"
    print(pad_box(content))

def log_spin(msg: str, status: str = "ok"):
    if status == "ok":
        tag = f"{BRIGHT_MAGENTA}➜ [SPIN    ]{RESET}"
        text = f"{BRIGHT_MAGENTA}{msg}{RESET}"
    else:
        tag = f"{BRIGHT_YELLOW}➜ [SPIN    ]{RESET}"
        text = f"{BRIGHT_YELLOW}{msg}{RESET}"
    content = f"{DIM}[{_timestamp()}]{RESET}   {tag} {text}"
    print(pad_box(content))

def log_task(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_GREEN}➜ [QUEST   ]{RESET} {msg}"
    print(pad_box(content))

def log_achievement(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_CYAN}★ [BADGE   ]{RESET} {BRIGHT_CYAN}{msg}{RESET}"
    print(pad_box(content))

def log_box(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_MAGENTA}🎁 [LOOTBOX ]{RESET} {msg}"
    print(pad_box(content))

def log_success(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_GREEN}{BOLD}✔ [SUCCESS ]{RESET} {BOLD}{BRIGHT_WHITE}{msg}{RESET}"
    print(pad_box(content))

def log_info(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {CYAN}ℹ [INFO    ]{RESET} {DIM}{msg}{RESET}"
    print(pad_box(content))

def log_warning(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_YELLOW}⚠ [WARN    ]{RESET} {YELLOW}{msg}{RESET}"
    print(pad_box(content))

def log_error(msg: str):
    content = f"{DIM}[{_timestamp()}]{RESET}   {BRIGHT_RED}{BOLD}✖ [ERROR   ]{RESET} {RED}{msg}{RESET}"
    print(pad_box(content))

def log_wallet_close():
    print(make_box_bottom(width=BOX_WIDTH))
    print()

# ============================================================================
# 6. MATHEMATICALLY ALIGNED MASTER EXECUTION TABLE & RECAP CARD
# ============================================================================
def print_summary_table(results: List[Dict[str, Any]], elapsed_seconds: float = 0.0):
    # 1. Title Header
    title_banner = f"{CYAN}┌{'─' * (BOX_WIDTH - 2)}┐{RESET}\n" + \
                   f"{CYAN}│{RESET}{BOLD}{BRIGHT_WHITE}{pad('📊 MASTER EXECUTION RECAP · COCONNECT HUB', BOX_WIDTH - 2, 'center')}{RESET}{CYAN}│{RESET}\n" + \
                   make_sep('├', '┬', '┤')

    print(title_banner)

    # 2. Table Column Headers
    hdr_cells = [f"{BOLD}{BRIGHT_CYAN}{pad(name, w, 'center')}{RESET}" for name, w, _ in TABLE_COLS]
    header_row = f"{CYAN}│ {RESET}" + f" {CYAN}│ {RESET}".join(hdr_cells) + f" {CYAN}│{RESET}"
    print(header_row)
    print(make_sep('├', '┼', '┤'))

    total_farmed_xp = 0
    total_badges = 0
    success_count = 0

    # 3. Table Rows
    for idx, r in enumerate(results, 1):
        cin_stat = r.get("checkin_status", "Skipped")
        if "claimed" in cin_stat.lower() or "+" in cin_stat:
            cin_colored = f"{BRIGHT_GREEN}{cin_stat}{RESET}"
        elif "cooldown" in cin_stat.lower():
            cin_colored = f"{BRIGHT_YELLOW}{cin_stat}{RESET}"
        else:
            cin_colored = f"{DIM}{cin_stat}{RESET}"

        spin_stat = r.get("spin_status", "Skipped")
        if "+" in spin_stat:
            spin_colored = f"{BRIGHT_MAGENTA}{spin_stat}{RESET}"
        elif "cooldown" in spin_stat.lower():
            spin_colored = f"{BRIGHT_YELLOW}{spin_stat}{RESET}"
        else:
            spin_colored = f"{DIM}{spin_stat}{RESET}"

        is_ok = (r.get("status") == "OK")
        if is_ok:
            success_count += 1
            stat_colored = f"{BRIGHT_GREEN}{BOLD}✔ OK{RESET}"
        else:
            stat_colored = f"{BRIGHT_RED}{BOLD}✖ FAIL{RESET}"

        xp_val = r.get("total_xp", 0)
        badges_val = r.get("badges_count", 0)
        streak_val = r.get("streak", 0)

        total_farmed_xp += xp_val
        total_badges += badges_val

        raw_handle = r.get("handle", "-")
        handle_display = f"@{raw_handle}" if not raw_handle.startswith("@") else raw_handle
        if len(handle_display) > 16:
            handle_display = handle_display[:15] + "…"

        row_vals = [
            f"{idx:02d}",
            r.get("address", "-"),
            handle_display,
            cin_colored,
            spin_colored,
            f"{BRIGHT_YELLOW}{streak_val} Hari{RESET}" if streak_val > 0 else f"{DIM}-{RESET}",
            f"{BRIGHT_CYAN}{badges_val} Badges{RESET}",
            f"{BRIGHT_GREEN}{BOLD}{xp_val:,} XP{RESET}",
            stat_colored
        ]

        cells = [pad(row_vals[i], TABLE_COLS[i][1], TABLE_COLS[i][2]) for i in range(len(TABLE_COLS))]
        print(f"{CYAN}│ {RESET}" + f" {CYAN}│ {RESET}".join(cells) + f" {CYAN}│{RESET}")

    # 4. Table Footer Summary Row
    left_w = sum(TABLE_COLS[i][1] + 3 for i in range(5)) - 1
    streak_w = TABLE_COLS[5][1] + 2
    badges_w = TABLE_COLS[6][1] + 2
    xp_w = TABLE_COLS[7][1] + 2
    status_w = TABLE_COLS[8][1] + 2

    footer_sep = f"{CYAN}├{'─' * left_w}┼{'─' * streak_w}┼{'─' * badges_w}┼{'─' * xp_w}┼{'─' * status_w}┤{RESET}"
    bot_line = f"{CYAN}└{'─' * left_w}┴{'─' * streak_w}┴{'─' * badges_w}┴{'─' * xp_w}┴{'─' * status_w}┘{RESET}"

    left_cell = pad(f" {BOLD}{BRIGHT_WHITE}TOTAL : {success_count}/{len(results)} AKUN BERHASIL DIKELOLA{RESET}", left_w - 2, "left")
    max_streak = max([r.get("streak", 0) for r in results]) if results else 0
    streak_cell = pad(f"{BRIGHT_YELLOW}{max_streak} Hari{RESET}" if max_streak > 0 else f"{DIM}-{RESET}", TABLE_COLS[5][1], "center")
    badges_cell = pad(f"{BRIGHT_CYAN}{total_badges} Badges{RESET}", TABLE_COLS[6][1], "center")
    xp_cell = pad(f"{BRIGHT_GREEN}{BOLD}{total_farmed_xp:,} XP{RESET}", TABLE_COLS[7][1], "right")
    rate_pct = int((success_count / len(results) * 100)) if results else 0
    status_cell = pad(f"{BRIGHT_GREEN}{BOLD}{rate_pct}%{RESET}", TABLE_COLS[8][1], "center")

    print(footer_sep)
    print(f"{CYAN}│ {RESET}{left_cell} {CYAN}│ {RESET}{streak_cell} {CYAN}│ {RESET}{badges_cell} {CYAN}│ {RESET}{xp_cell} {CYAN}│ {RESET}{status_cell} {CYAN}│{RESET}")
    print(bot_line)
    print()

    # 5. Finish Recap Card Panel
    mins = int(elapsed_seconds // 60)
    secs = int(elapsed_seconds % 60)
    time_str = f"{mins} Menit {secs} Detik" if mins > 0 else f"{secs} Detik"
    avg_xp = (total_farmed_xp / len(results)) if results else 0

    print(make_box_top("[ LAPORAN REKAPITULASI EKSEKUSI SELESAI ]", width=BOX_WIDTH, border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Total Akun Dikelola   :{RESET} {BOLD}{BRIGHT_CYAN}{len(results)} Wallets{RESET}  {DIM}({BRIGHT_GREEN}{success_count}/{len(results)} Sukses - {rate_pct}%{RESET}{DIM}){RESET}", border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Total Akumulasi XP    :{RESET} {BOLD}{BRIGHT_GREEN}{total_farmed_xp:,} XP{RESET}  {DIM}(Rata-rata: {avg_xp:,.1f} XP / Akun){RESET}", border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Total Badge Diklaim   :{RESET} {BOLD}{BRIGHT_CYAN}{total_badges} Badges{RESET}  {DIM}(OG Badge & Road to 80K XP){RESET}", border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Total Waktu Eksekusi  :{RESET} {BOLD}{BRIGHT_YELLOW}{time_str}{RESET}", border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Status Siklus Harian  :{RESET} {BOLD}{BRIGHT_YELLOW}Seluruh akun dalam cooldown (~18 jam){RESET}", border_col=BRIGHT_GREEN))
    print(pad_box(f"{BOLD}{WHITE}Jadwal Rutin Besok    :{RESET} {BRIGHT_WHITE}Jalankan kembali besok pagi: {BRIGHT_CYAN}{BOLD}python main.py{RESET}", border_col=BRIGHT_GREEN))
    print(make_box_bottom(width=BOX_WIDTH, border_col=BRIGHT_GREEN))
    print()
