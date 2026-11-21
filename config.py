import os

# Base URL dApp
BASE_URL = "https://hub.coconnect.co"

# Chain & SIWE settings
CHAIN_ID = 1
STATEMENT = "Sign in to CoConnect Hub"

# Delay settings (detik antar wallet untuk anti-sybil / random jitter)
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 5

# Automation features toggle
AUTO_SET_PROFILE = True       # Otomatis isi username & avatar jika belum selesai
AUTO_DAILY_CHECKIN = True     # Otomatis daily check-in
AUTO_SPIN_WHEEL = True        # Otomatis putar spin wheel daily
AUTO_SOLVE_TASKS = True       # Otomatis kerjakan task instant (visit link & quiz multiple-choice)
AUTO_CLAIM_ACHIEVEMENTS = True # Otomatis claim achievement jika ada yang selesai

# File paths
PRIVATE_KEYS_FILE = "private_keys.txt"
PROXIES_FILE = "proxies.txt"
