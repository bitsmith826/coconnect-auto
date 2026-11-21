# 🚀 CoConnect Hub Automation Suite

Sistem otomasi multi-wallet berbasis Python untuk interaksi terprogram dengan platform **CoConnect Hub** (`https://hub.coconnect.co`), dibangun dengan reverse engineering arsitektur dApp Web3 modern (Next.js + Supabase + Viem EIP-4361 SIWE).

---

> ### ⚠️ DISCLAIMER & TUJUAN EDUKASI (*EDUCATIONAL PURPOSES ONLY*)
> Repositori ini dibuat dan dipublikasikan semata-mata untuk **tujuan edukasi, penelitian keamanan software, dan studi arsitektur sistem Web3**.
> 
> * **Riset Protokol Otentikasi**: Studi kasus implementasi standar kriptografi Ethereum [EIP-4361 (Sign-In with Ethereum / SIWE)](https://eips.ethereum.org/EIPS/eip-4361) dan EIP-191 `personal_sign` menggunakan Python tanpa ketergantungan browser headless.
> * **Manajemen Sesi & Resilience**: Analisis penanganan sesi cookie HTTP-only, retry backoff adaptif pada rate-limit HTTP 429 (`Retry-After`), dan mitigasi error jaringan.
> * **Tanggung Jawab Pengguna**: Pengembang dan kontributor tidak bertanggung jawab atas segala bentuk penyalahgunaan, pelanggaran syarat layanan pihak ketiga (*Terms of Service*), suspensi akun, atau kerugian material/non-material yang timbul dari penggunaan repositori ini. Gunakan hanya pada akun pengujian (*test/burner accounts*) Anda sendiri.

---

## ⚡ Fitur Utama

1. **Auto EIP-4361 SIWE Sign-In (Ethereum & EVM)**:
   - Request nonce kriptografis ke `/api/auth/nonce`.
   - Menghasilkan pesan SIWE terstandarisasi EIP-4361 sesuai spesifikasi Viem frontend.
   - Penandatanganan pesan offline lokal menggunakan private key tanpa membuka browser.
   - Manajemen cookie sesi dApp (`hub_session`) secara otomatis.
2. **Auto Profile Setup & Dynamic Niches**:
   - Menghasilkan username unik natural (3–20 karakter).
   - Mengatur avatar default valid ke preferensi profil.
   - Memetakan 4 kategori *niches* akun secara deterministik dari 14 kategori platform untuk memenuhi syarat campaign khusus.
3. **Auto Daily Check-In & Streak Keeper**:
   - Klaim daily streak reward langsung ke endpoint `/api/daily` (`kind: checkin`).
   - Melacak streak hari berturut-turut dengan parsing cooldown presisi.
4. **Auto Daily Spin Wheel**:
   - Memutar roda keberuntungan harian `/api/daily` (`kind: spin`).
   - Mendeteksi dan mengeksekusi bonus putaran gratis secara otomatis (`again: true`).
5. **Instant Tasks Solver**:
   - Menyelesaikan task yang dapat diverifikasi instan (kunjungan tautan unduhan dan kuis multiple-choice).
   - Memfilter task photo submission dari dummy upload untuk menjaga reputasi akun dan integritas anti-sybil.
6. **Desain Arsitektur Aman & Anti-Detection**:
   - Impersonasi TLS & HTTP/2 browser Chrome (`curl_cffi` Chrome 120 profile).
   - Random jitter delay antar akun dan antar task.
   - Pembersihan descriptor socket/session di setiap siklus akun.
   - Proteksi ketat private key lokal (tidak pernah dikirim ke server pihak ketiga).

---

## 📁 Struktur Direktori

```
coconnect-auto/
├── config.py                 # Pengaturan global, chain, & delay
├── main.py                   # Runner utama (full automation)
├── run_daily.py              # Runner siklus harian (checkin & spin wheel)
├── requirements.txt          # Dependensi Python
├── private_keys.txt.example  # Contoh template private key
├── proxies.txt.example       # Contoh template proxy
├── .gitignore                # Filter proteksi file sensitif & cache
└── src/
    ├── bot.py                # Worker CoConnect per wallet
    ├── client.py             # HTTP client dengan curl_cffi & retry backoff
    ├── siwe.py               # Generator pesan SIWE & local signature EIP-191
    ├── tasks.py              # Handler daily checkin, spin, niches, & tasks
    └── logger.py             # Visual CLI dashboard dengan wcwidth padding
```

---

## 🛠️ Cara Penggunaan

### 1. Instalasi Dependensi
Pastikan Python 3.9+ sudah terpasang, lalu pasang paket dependensi:
```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Private Key
Buat file `private_keys.txt` di root folder (bisa menyalin dari `private_keys.txt.example`):
```bash
# Isi 1 baris per private key EVM wallet (burner):
0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
```
> 🔒 **CATATAN KEAMANAN**: File `private_keys.txt` sudah otomatis diabaikan oleh `.gitignore` sehingga tidak akan pernah terunggah ke Git. Jangan pernah membagikan private key Anda kepada siapapun!

### 3. (Opsional) Konfigurasi Proxy
Jika mengelola banyak akun dan ingin menggunakan multi-IP, buat file `proxies.txt`:
```
http://username:password@123.45.67.89:8080
socks5://username:password@98.76.54.32:1080
```

### 4. Menjalankan Bot
Untuk menjalankan seluruh alur otomatisasi (SIWE login, setup profil, daily check-in, spin wheel, instant tasks, dan klaim badge):
```bash
python main.py
```

Untuk menjalankan siklus klaim harian rutin:
```bash
python run_daily.py
```

---

## 🐙 Panduan Mengunggah ke GitHub (*Step-by-Step Push Guide*)

Berikut langkah demi langkah untuk mengunggah repositori ini ke akun GitHub Anda:

### Langkah 1: Buat Repositori Baru di GitHub
1. Buka browser dan login ke akun GitHub Anda di [github.com](https://github.com).
2. Klik ikon **+** di pojok kanan atas, lalu pilih **New repository** (atau akses langsung ke [github.com/new](https://github.com/new)).
3. Beri nama repositori, misalnya: `coconnect-auto`.
4. Pilih visibilitas repositori:
   * **Private** (Disarankan jika Anda ingin kode hanya bisa diakses sendiri).
   * **Public** (Jika ingin dibagikan secara terbuka untuk portofolio).
5. **JANGAN centang** *"Add a README file"*, *"Add .gitignore"*, atau *"Choose a license"* (karena file-file ini sudah tersedia di proyek lokal Anda).
6. Klik tombol hijau **Create repository**.
7. Salin URL repositori yang muncul (misalnya: `https://github.com/USERNAME/coconnect-auto.git`).

---

### Langkah 2: Eksekusi Git di Terminal Lokal
Buka PowerShell atau Command Prompt di folder proyek `d:\Coding\coconnect-auto`, lalu jalankan baris perintah berikut:

```bash
# 1. Tambahkan semua file proyek yang aman ke Git staging
git add .

# 2. Buat commit perdana
git commit -m "feat: initial release of coconnect-auto suite with siwe, daily streak, and anti-sybil resilience"

# 3. Ubah nama branch utama menjadi main
git branch -M main

# 4. Hubungkan repositori lokal ke GitHub Anda (ganti URL di bawah dengan URL repo Anda)
git remote add origin https://github.com/USERNAME/coconnect-auto.git

# 5. Unggah (push) kode ke GitHub
git push -u origin main
```

> 💡 **TIPS OTENTIKASI GITHUB**:
> Jika GitHub meminta password saat `git push`, gunakan **Personal Access Token (Classic)** sebagai password (bukan password akun GitHub Anda).
> Cara membuatnya: Buka **GitHub Settings** → **Developer Settings** → **Personal Access Tokens** → **Tokens (classic)** → **Generate new token** → centang scope `repo` → salin token yang dihasilkan.

---

## 📊 Tampilan Dashboard Terminal

Bot dilengkapi tampilan visual CLI berpresisi tinggi dengan deteksi lebar karakter `wcwidth`:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    📊 MASTER EXECUTION RECAP · COCONNECT HUB                                     │
├─────┬───────────────┬──────────────────┬────────────────┬────────────────┬────────┬──────────┬──────────┬────────┤
│ No  │    Address    │     Username     │    Check-In    │   Spin Wheel   │ Streak │  Badges  │ Total XP │ Status │
├─────┼───────────────┼──────────────────┼────────────────┼────────────────┼────────┼──────────┼──────────┼────────┤
│ 01  │ 0x1A2b...9F0e │ @alpha_hunter_01 │     +5 XP      │     +10 XP     │ 2 Hari │ 2 Badges │   431 XP │  ✔ OK  │
│ 02  │ 0x8C3d...4E2a │ @crypto_vault_02 │     +5 XP      │     +50 XP     │ 2 Hari │ 2 Badges │   480 XP │  ✔ OK  │
├──────────────────────────────────────────────────────────────────────────┼────────┼──────────┼──────────┼────────┤
│  TOTAL : 2/2 AKUN BERHASIL DIKELOLA                                      │ 2 Hari │ 4 Badges │   911 XP │  100%  │
└──────────────────────────────────────────────────────────────────────────┴────────┴──────────┴──────────┴────────┘
```
