import time
import re
from typing import Dict, Any, Optional
from eth_account import Account
from web3 import Web3

from config import (
    BASE_URL,
    AUTO_SET_PROFILE,
    AUTO_DAILY_CHECKIN,
    AUTO_SPIN_WHEEL,
    AUTO_SOLVE_TASKS,
    AUTO_CLAIM_ACHIEVEMENTS
)
from src.client import CoConnectClient
from src.siwe import create_siwe_message, sign_siwe_message
from src.tasks import (
    setup_profile_if_needed,
    claim_daily_checkin,
    spin_daily_wheel,
    solve_instant_tasks,
    claim_all_achievements,
    open_unlocked_boxes,
    adopt_and_refresh_wallet
)
from src.logger import (
    log_wallet_header,
    log_wallet_close,
    log_auth,
    log_profile,
    log_checkin,
    log_spin,
    log_task,
    log_achievement,
    log_box,
    log_success,
    log_info,
    log_warning,
    log_error
)

class CoConnectBot:
    def __init__(self, private_key: str, proxy: Optional[str] = None):
        private_key = private_key.strip().strip("'\"")
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        self.private_key = private_key
        self.proxy = proxy
        
        # Derive address securely
        account = Account.from_key(self.private_key)
        self.address = Web3.to_checksum_address(account.address)
        self.client = CoConnectClient(proxy=self.proxy)

    def login(self) -> bool:
        """Melakukan otentikasi SIWE ke CoConnect Hub dengan proteksi error."""
        try:
            # 1. Dapatkan nonce
            nonce_url = f"{BASE_URL}/api/auth/nonce"
            resp = self.client.get(nonce_url)
            if resp.status_code != 200:
                log_error(f"Gagal mengambil nonce (HTTP {resp.status_code})")
                return False
                
            nonce_data = self.client.safe_json(resp)
            if not nonce_data.get("ok") or not nonce_data.get("nonce"):
                log_error(f"Response nonce invalid: {nonce_data}")
                return False
                
            nonce = nonce_data["nonce"]

            # 2. Buat pesan SIWE & tanda tangani secara lokal
            siwe_msg = create_siwe_message(address=self.address, nonce=nonce)
            sig = sign_siwe_message(message=siwe_msg, private_key=self.private_key)

            # 3. Kirim ke /api/auth/wallet
            auth_url = f"{BASE_URL}/api/auth/wallet"
            auth_payload = {
                "chain": "ethereum",
                "message": siwe_msg,
                "signature": sig
            }
            auth_resp = self.client.post(auth_url, json=auth_payload)
            auth_data = self.client.safe_json(auth_resp)
            if auth_resp.status_code == 200 and auth_data.get("ok"):
                return True
                
            log_error(f"Otentikasi gagal: {auth_data.get('error', auth_resp.text)}")
            return False
        except Exception as e:
            log_error(f"Koneksi auth error: {e}")
            return False

    def run(self, wallet_num: int = 1, total_wallets: int = 1) -> Dict[str, Any]:
        """Menjalankan seluruh alur otomatisasi untuk 1 wallet secara presisi."""
        short_addr = f"{self.address[:6]}...{self.address[-4:]}"
        result = {
            "address": short_addr,
            "full_address": self.address,
            "handle": "-",
            "checkin_status": "Skipped",
            "spin_status": "Skipped",
            "tasks_done": 0,
            "badges_count": 0,
            "loot_box_status": "-",
            "streak": 0,
            "total_xp": 0,
            "status": "FAIL"
        }

        log_wallet_header(wallet_num, total_wallets, short_addr)
        if self.proxy:
            log_info(f"Proxy: {self.proxy}")

        # 1. Login SIWE
        if not self.login():
            result["status"] = "AUTH_FAIL"
            log_wallet_close()
            self.client.close()
            return result
        log_auth("Sesi SIWE terverifikasi (hub_session aktif)")

        # 2. Ambil data profil (/api/me)
        try:
            me_resp = self.client.get(f"{BASE_URL}/api/me")
            if me_resp.status_code != 200:
                log_error(f"Gagal mengambil profil akun (/api/me)")
                result["status"] = "ME_FAIL"
                log_wallet_close()
                self.client.close()
                return result
                
            me_data = self.client.safe_json(me_resp)
            profile = me_data.get("profile", {})
            handle = profile.get("handle", "-")
            result["handle"] = handle
            result["total_xp"] = profile.get("xp", 0)
            result["badges_count"] = len(me_data.get("badges", []))
            
            member_str = ""
            try:
                num_resp = self.client.get(f"{BASE_URL}/api/me/member-number")
                num_data = self.client.safe_json(num_resp)
                if num_data.get("ok") and num_data.get("number"):
                    member_str = f" (#{num_data.get('number')})"
            except Exception:
                pass

            log_profile(f"Username: @{handle}{member_str} | Saldo: {result['total_xp']} XP")
        except Exception as e:
            log_error(f"Error pembacaan profil: {e}")
            result["status"] = "ME_ERROR"
            log_wallet_close()
            self.client.close()
            return result

        # 3. Setup Profile jika belum selesai
        if AUTO_SET_PROFILE:
            try:
                if setup_profile_if_needed(self.client, me_data, self.address):
                    time.sleep(1)
                    updated_me = self.client.safe_json(self.client.get(f"{BASE_URL}/api/me"))
                    result["handle"] = updated_me.get("profile", {}).get("handle", handle)
                    niches_list = updated_me.get("profile", {}).get("niches", [])
                    if niches_list:
                        niches_str = ", ".join(niches_list[:3])
                        log_profile(f"Profile diset: @{result['handle']} │ Niches: [{niches_str}]")
                    else:
                        log_profile(f"Username diset: @{result['handle']}")
            except Exception:
                pass

        # 4. Adopt & Link Wallet ke Onboarding
        adopt_and_refresh_wallet(self.client, self.address)

        # 5. Daily Check-In
        if AUTO_DAILY_CHECKIN:
            cin_res = claim_daily_checkin(self.client)
            if cin_res.get("ok"):
                result["checkin_status"] = f"+{cin_res.get('xp', 5)} XP"
                streak = cin_res.get("streak", 1)
                result["streak"] = streak
                log_checkin(f"Berhasil klaim +{cin_res.get('xp', 5)} XP (Streak: {streak} Hari)", status="ok")
            elif cin_res.get("cooldown"):
                result["checkin_status"] = cin_res.get("display", "Cooldown")
                time_hint = cin_res.get("error", "").replace("You can check in again in ", "").rstrip(".")
                log_checkin(f"Cooldown aktif (Tersedia kembali: {time_hint})", status="cooldown")
            else:
                result["checkin_status"] = "Failed"
                log_warning(f"Check-In: {cin_res.get('error')}")

        # 6. Spin Daily Wheel
        if AUTO_SPIN_WHEEL:
            spin_res = spin_daily_wheel(self.client)
            if spin_res.get("ok"):
                result["spin_status"] = f"+{spin_res.get('xp', 0)} XP"
                log_spin(f"Roda berputar: +{spin_res.get('xp', 0)} XP", status="ok")
            elif spin_res.get("cooldown"):
                result["spin_status"] = spin_res.get("display", "Cooldown")
                time_hint = spin_res.get("error", "").replace("You can spin again in ", "").rstrip(".")
                log_spin(f"Cooldown aktif (Tersedia kembali: {time_hint})", status="cooldown")
            else:
                result["spin_status"] = "Failed"
                log_warning(f"Spin Wheel: {spin_res.get('error')}")

        # 7. Kerjakan Instant Tasks (Link & Quiz)
        if AUTO_SOLVE_TASKS:
            try:
                task_res = solve_instant_tasks(self.client)
                success_tasks = [t for t in task_res if t.get("status") == "success"]
                result["tasks_done"] = len(success_tasks)
                for st in success_tasks:
                    log_task(f"{st.get('title')} (+{st.get('points', 0)} XP)")
            except Exception as e:
                log_warning(f"Task solver notice: {e}")

        # 8. Klaim Achievements & Buka Loot Boxes
        if AUTO_CLAIM_ACHIEVEMENTS:
            try:
                ach_claimed = claim_all_achievements(self.client)
                for ac in ach_claimed:
                    log_achievement(f"{ac.get('name')} (+{ac.get('xp', 0)} XP & Badge)")
                
                boxes_opened = open_unlocked_boxes(self.client)
                for bo in boxes_opened:
                    rew = bo.get("reward", {})
                    xp_rew = rew.get("xp", 0)
                    rarity = rew.get("rarity", "common").capitalize()
                    result["loot_box_status"] = f"+{xp_rew} XP"
                    log_box(f"{bo.get('name')}: +{xp_rew} XP ({rarity})")
            except Exception as e:
                log_warning(f"Box/Achievement notice: {e}")

        # 9. Ambil data akhir untuk pelaporan akurat
        try:
            final_me = self.client.get(f"{BASE_URL}/api/me")
            if final_me.status_code == 200:
                final_data = self.client.safe_json(final_me)
                result["total_xp"] = final_data.get("profile", {}).get("xp", result["total_xp"])
                result["badges_count"] = len(final_data.get("badges", []))
                
            # Ambil streak dari /api/daily jika belum terisi
            daily_data = self.client.safe_json(self.client.get(f"{BASE_URL}/api/daily")).get("daily", {})
            result["streak"] = daily_data.get("checkin", {}).get("streak", result["streak"])
        except Exception:
            pass

        log_success(f"Akun selesai diproses │ Saldo: {result['total_xp']:,} XP │ Streak: {result['streak']} Hari │ Badges: {result['badges_count']}")
        log_wallet_close()
        self.client.close()
        result["status"] = "OK"
        return result
