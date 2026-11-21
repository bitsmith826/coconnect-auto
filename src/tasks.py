import random
import time
import re
from typing import Dict, Any, List
from config import BASE_URL

# A clean 1x1 valid PNG in base64 to serve as valid avatar upload
DEFAULT_AVATAR = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

PREFIXES = ["crypt", "alpha", "defi", "web3", "block", "node", "nexus", "sat", "sol", "eth", "byte", "apex"]
SUFFIXES = ["hunter", "farmer", "vault", "pro", "master", "wave", "drop", "pilot", "runner", "hub"]

# 14 Valid Niches reverse-engineered from Turbopack module 462719
ALL_NICHES = [
    "ai_agents", "airdrop", "defi", "tradfi", "socialfi",
    "depin", "gamefi", "nft", "memes", "perps",
    "prediction_markets", "rwa", "trading", "betting"
]

def pick_niches_for_address(address: str, count: int = 4) -> List[str]:
    """Menghasilkan kombinasi niche deterministik berdasarkan address wallet."""
    try:
        seed = int(address[-6:], 16)
    except Exception:
        seed = 42
    rng = random.Random(seed)
    return rng.sample(ALL_NICHES, min(count, len(ALL_NICHES)))

def generate_random_handle(address: str) -> str:
    """Menghasilkan username realistis 3-20 karakter."""
    p = random.choice(PREFIXES)
    s = random.choice(SUFFIXES)
    short_addr = address[-4:].lower()
    handle = f"{p}_{s}_{short_addr}"
    if len(handle) > 20:
        handle = handle[:20]
    return handle

def setup_profile_if_needed(client, me_data: Dict[str, Any], address: str) -> bool:
    """
    Menyiapkan username, avatar, dan preferensi niches akun jika belum lengkap.
    """
    try:
        profile = me_data.get("profile", {})
        onboarding = me_data.get("onboarding", {})
        profile_done = onboarding.get("done", {}).get("profile", False)
        existing_niches = profile.get("niches", [])
        
        url = f"{BASE_URL}/api/me/preferences"
        payload = {}
        
        if not profile_done:
            payload["handle"] = generate_random_handle(address)
            payload["avatarUrl"] = DEFAULT_AVATAR
            
        if not existing_niches:
            payload["niches"] = pick_niches_for_address(address, count=4)
            
        if payload:
            resp = client.patch(url, json=payload)
            data = client.safe_json(resp)
            if resp.status_code == 200 and data.get("ok"):
                return True
    except Exception:
        pass
    return False

def parse_cooldown(error_msg: str) -> str:
    """Ekstraksi waktu jeda cooldown ringkas (misal: '23h 48m' -> 'Cooldown (23h)', '53m' -> 'Cooldown (53m)')."""
    h_match = re.search(r'(\d+)\s*h', error_msg, re.I)
    if h_match:
        return f"Cooldown ({h_match.group(1)}h)"
    m_match = re.search(r'(\d+)\s*m', error_msg, re.I)
    if m_match:
        return f"Cooldown ({m_match.group(1)}m)"
    return "Cooldown"

def claim_daily_checkin(client) -> Dict[str, Any]:
    """
    Melakukan klaim Daily Check-In streak harian dengan handling error & cooldown.
    """
    url = f"{BASE_URL}/api/daily"
    try:
        resp = client.post(url, json={"kind": "checkin"})
        data = client.safe_json(resp)
        
        if data.get("ok"):
            return {
                "ok": True,
                "cooldown": False,
                "xp": data.get("xp", 5),
                "streak": data.get("streak", 1),
                "bonus": data.get("bonus", 0),
                "raw": data
            }
        
        err = data.get("error", "Request failed")
        is_cd = any(w in err.lower() for w in ["again in", "already", "tomorrow", "claimed"])
        return {
            "ok": False,
            "cooldown": is_cd,
            "display": parse_cooldown(err) if is_cd else "Failed",
            "error": err
        }
    except Exception as e:
        return {
            "ok": False,
            "cooldown": False,
            "display": "Error",
            "error": str(e)
        }

def spin_daily_wheel(client) -> Dict[str, Any]:
    """
    Memutar Daily Wheel untuk bonus XP dengan handling error & cooldown.
    """
    url = f"{BASE_URL}/api/daily"
    total_spin_xp = 0
    spins_done = 0
    
    try:
        while True:
            resp = client.post(url, json={"kind": "spin"})
            data = client.safe_json(resp)
            
            if not data.get("ok"):
                err = data.get("error", "No spins available")
                is_cd = any(w in err.lower() for w in ["again in", "already", "tomorrow", "claimed"])
                
                # Jika sudah pernah spin sebelumnya dalam loop ini, kembalikan hasil spin
                if spins_done > 0:
                    return {
                        "ok": True,
                        "cooldown": False,
                        "xp": total_spin_xp,
                        "spins_done": spins_done,
                        "display": f"+{total_spin_xp} XP"
                    }
                    
                return {
                    "ok": False,
                    "cooldown": is_cd,
                    "display": parse_cooldown(err) if is_cd else "No Spins",
                    "error": err
                }
            
            xp_won = data.get("xp", 0)
            total_spin_xp += xp_won
            spins_done += 1
            
            # Jika dapat kesempatan putar lagi (again: true)
            if data.get("again"):
                time.sleep(1.5)
                continue
            else:
                return {
                    "ok": True,
                    "cooldown": False,
                    "xp": total_spin_xp,
                    "spins_done": spins_done,
                    "display": f"+{total_spin_xp} XP"
                }
    except Exception as e:
        if spins_done > 0:
            return {"ok": True, "cooldown": False, "xp": total_spin_xp, "spins_done": spins_done, "display": f"+{total_spin_xp} XP"}
        return {"ok": False, "cooldown": False, "display": "Error", "error": str(e)}

def solve_instant_tasks(client) -> List[Dict[str, Any]]:
    """
    Mendeteksi dan menyelesaikan task instant tanpa error fatal:
    - Visit link (misal: Download Talisman Mobile)
    - Multiple-choice quiz text (misal: Farside automated trading question)
    Catatan: Task photo tidak disubmit otomatis untuk mencegah penolakan dari sistem AI verifikasi.
    """
    results = []
    try:
        # 1. Ambil daftar submission user saat ini
        sub_resp = client.get(f"{BASE_URL}/api/submissions")
        completed_task_ids = set()
        if sub_resp.status_code == 200:
            for s in client.safe_json(sub_resp).get("submissions", []):
                if s.get("status") in ["approved", "submitted", "pending"]:
                    completed_task_ids.add(s.get("taskId"))
                    
        # 2. Ambil katalog campaign
        cat_resp = client.get(f"{BASE_URL}/api/catalogue")
        if cat_resp.status_code != 200:
            return results
            
        campaigns = client.safe_json(cat_resp).get("campaigns", [])
        
        for c in campaigns:
            for t in c.get("tasks", []):
                tid = t.get("id")
                ttype = t.get("type")
                title = t.get("title")
                
                if tid in completed_task_ids:
                    continue
                    
                payload = None
                if ttype == "visit_link":
                    payload = {}
                elif ttype == "text" and t.get("config", {}).get("answerLength") == "choice":
                    choices = t.get("config", {}).get("choices", [])
                    if choices:
                        payload = {"text": choices[0]}
                # Note: 'photo' tasks are excluded because the platform performs
                # AI vision verification (photoCheck) and dummy uploads lead to rejected status.
                        
                if payload is not None:
                    time.sleep(random.uniform(0.8, 1.8))
                    try:
                        res = client.post(f"{BASE_URL}/api/submissions", json={
                            "taskId": tid,
                            "payload": payload
                        })
                        res_data = client.safe_json(res)
                        if res_data.get("ok"):
                            results.append({
                                "taskId": tid,
                                "title": title,
                                "status": "success",
                                "points": t.get("points", 0)
                            })
                    except Exception:
                        pass
    except Exception:
        pass
                    
    return results

def claim_all_achievements(client) -> List[Dict[str, Any]]:
    """
    Mengecek dan mengklaim semua achievement yang berstatus claimable: true
    (seperti OG Badge, Road to 80K XP, dll) dengan aman.
    """
    claimed = []
    try:
        r = client.get(f"{BASE_URL}/api/achievements")
        if r.status_code != 200:
            return claimed
        data = client.safe_json(r)
        for ach in data.get("achievements", []):
            if ach.get("claimable"):
                ach_id = ach.get("id")
                ach_name = ach.get("name")
                try:
                    c_resp = client.post(f"{BASE_URL}/api/achievements/claim", json={"achievementId": ach_id})
                    c_data = client.safe_json(c_resp)
                    if c_resp.status_code == 200 and c_data.get("ok"):
                        claimed.append({"id": ach_id, "name": ach_name, "xp": c_data.get("xp", 0)})
                except Exception:
                    pass
    except Exception:
        pass
    return claimed

def open_unlocked_boxes(client) -> List[Dict[str, Any]]:
    """
    Membuka seluruh loot box / crates yang statusnya sudah unlocked.
    """
    opened = []
    try:
        r = client.get(f"{BASE_URL}/api/boxes")
        if r.status_code != 200:
            return opened
        boxes = client.safe_json(r).get("boxes", [])
        for b in boxes:
            if b.get("unlocked"):
                b_id = b.get("id")
                b_name = b.get("name")
                try:
                    o_resp = client.post(f"{BASE_URL}/api/boxes/open", json={"boxId": b_id})
                    o_data = client.safe_json(o_resp)
                    if o_resp.status_code == 200 and o_data.get("ok"):
                        reward = o_data.get("reward", {})
                        opened.append({"id": b_id, "name": b_name, "reward": reward})
                except Exception:
                    pass
    except Exception:
        pass
    return opened

def adopt_and_refresh_wallet(client, address: str) -> bool:
    """
    Mendaftarkan wallet login ke daftar wallets terhubung
    dan memperbarui snapshot on-chain.
    """
    try:
        r = client.post(f"{BASE_URL}/api/wallet/adopt", json={"walletName": "MetaMask"})
        if r.status_code == 200 and client.safe_json(r).get("ok"):
            try:
                client.post(f"{BASE_URL}/api/wallet/refresh")
            except Exception:
                pass
            return True
    except Exception:
        pass
    return False
