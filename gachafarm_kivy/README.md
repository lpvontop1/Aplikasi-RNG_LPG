# 🌿 GachaFarm Simulator — Kivy (Android)

Konversi aplikasi simulasi panen tanaman berbasis gacha (distribusi Poisson, mutasi, harga dinamis) dari **Python Tkinter** ke **Kivy + Buildozer** untuk Android.

Semua logika perhitungan (Poisson, `generate_fruit_count`, `kalkulasi_berat_eksponensial`, `kalkulasi_harga_dinamis`, `simulasi_mutasi`, algoritma alpha) **IDENTIK** dengan versi Tkinter asli. Hanya antarmuka pengguna yang diadaptasi untuk layar sentuh Android.

---

## 📦 Struktur Proyek

```
gachafarm_kivy/
├── main.py              # Kode utama (logika + UI Kivy dalam satu file)
├── shop.json            # Data bawaan tanaman & mutasi (disertakan dalam APK)
├── buildozer.spec       # Konfigurasi build Android (minSdk 24, target 34)
├── requirements.txt     # Dependensi desktop untuk testing
└── README.md            # Dokumen ini
```

Setelah aplikasi pertama kali dijalankan di Android, file data custom akan dibuat di **internal storage** perangkat:

```
/data/data/org.gachafarm.simulator/files/
└── data/
    ├── shop_custom.json    # Hasil edit tanaman dari tab Katalog
    └── mutasi_custom.json  # Hasil edit chance/multiplier mutasi
```

---

## 🚀 Cara Menjalankan di Desktop (untuk Testing)

### 1. Install Kivy

```bash
pip install -r requirements.txt
```

### 2. Jalankan aplikasi

```bash
python main.py
```

Window akan otomatis di-set ke ukuran 412×915 (mirip Pixel 6) untuk simulasi layar ponsel.

> ⚠️ **Catatan**: Pastikan `shop.json` berada di folder yang sama dengan `main.py`. Pada desktop, file custom akan dibuat di `./app_data/data/`.

---

## 📱 Cara Build APK untuk Android

### 1. Prasyarat Sistem

Buildozer memerlukan **Linux** (atau WSL2 di Windows). Berikut dependensi sistem yang harus diinstall sebelumnya:

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
    cmake libffi-dev libssl-dev build-essential ccache
```

**Fedora / RHEL:**
```bash
sudo dnf install -y git zip unzip java-17-openjdk-devel python3-pip autoconf \
    libtool pkgconfig zlib-devel ncurses-devel cmake libffi-devel openssl-devel \
    gcc gcc-c++ ccache
```

### 2. Install Buildozer

```bash
pip install buildozer==1.5.0
# atau versi terbaru:
pip install --upgrade buildozer
```

### 3. Build APK Debug

Dari dalam folder proyek (yang berisi `main.py`, `shop.json`, `buildozer.spec`):

```bash
cd gachafarm_kivy
buildozer android debug
```

Build pertama akan **makan waktu 30–60 menit** karena buildozer akan:
1. Download Android SDK + NDK (~2 GB)
2. Build Python untuk Android dari source
3. Build Kivy dari source
4. Bundle semua dependency ke APK

Build selanjutnya hanya butuh 2–5 menit (cache).

### 4. Hasil Build

APK akan muncul di folder `bin/`:

```
bin/
└── gachafarm-1.0.0-debug.apk
```

### 5. Install ke Perangkat Android

**Opsi A — Via ADB (disarankan):**

```bash
# Aktifkan USB Debugging di Android (Developer Options)
# Hubungkan ponsel via USB

# Cek perangkat terdeteksi:
adb devices

# Install APK:
adb install -r bin/gachafarm-1.0.0-debug.apk
```

**Opsi B — Via deploy langsung dari buildozer:**

```bash
buildozer android debug deploy run
```

Perintah ini akan: build → install ke perangkat terhubung → jalankan aplikasi → tampilkan log.

**Opsi C — Manual:**
Copy file `bin/gachafarm-1.0.0-debug.apk` ke ponsel, lalu install (izinkan "Install from unknown sources").

### 6. Lihat Log (untuk debugging)

```bash
# Lihat log realtime dari aplikasi yang sedang berjalan
adb logcat -s python:stdout python:stderr

# Atau via buildozer:
buildozer android logcat
```

---

## 🔁 Build Release (untuk Google Play)

Untuk build APK/AAB yang siap upload ke Play Store:

```bash
# 1. Generate keystore (sekali saja)
keytool -genkey -v -keystore gachafarm.keystore -alias gachafarm \
    -keyalg RSA -keysize 2048 -validity 10000

# 2. Edit buildozer.spec — uncomment dan set:
#   android.release_artifact = aab
#   android.signing_release = True
#   (lalu jalankan ulang build release)

# 3. Build release AAB
buildozer android release
```

---

## ✨ Fitur Aplikasi

### Tab Simulasi
- **Spinner Kategori** — pilih "Sekali Tanam, Panen Berkali-kali" atau "Sekali Tanam, Sekali Panen"
- **Spinner Tanaman** — daftar tanaman dari kategori terpilih, dengan tier
- **Kartu Preview** — menampilkan statistik tanaman terpilih (durasi, hasil, berat, harga)
- **Input Waktu Tanam** — format `YYYY-MM-DD HH:MM`, otomatis menghitung estimasi panen + countdown realtime
- **Input Iterasi** — 1 sampai 100.000 siklus
- **Slider Luck (Alpha)** — dari -1.0 (Sangat Sulit) sampai +1.0 (Sangat Mudah), dengan label dinamis
- **Tombol Jalankan** — menjalankan simulasi di background thread + loading popup
- **Tombol Reset** — reset semua input ke default
- **Area Hasil** — kartu statistik, tabel per-iterasi, tabel per-buah, dan grand total

### Tab Katalog
- **Sub-tab Tanaman** — daftar semua tanaman (110 item) dengan field editable:
  - Nama tanaman, Tier (E/D/C/B/A), Durasi, Hasil panen, Berat rata-rata, Harga bibit, Harga jual
- **Sub-tab Mutasi** — daftar 12 mutasi dengan chance & multiplier editable
- **Tombol Simpan** — menyimpan semua perubahan ke `shop_custom.json` & `mutasi_custom.json` di internal storage
- **Tombol Kembalikan ke Default** — hapus file custom, reload dari `shop.json` bawaan APK

### Storage Otomatis
- Saat aplikasi pertama kali dijalankan, file custom belum ada → otomatis pakai `shop.json` bawaan APK
- Setiap kali user klik **Simpan** di tab Katalog, file custom dibuat/overwrite
- Saat simulasi dijalankan, data dibaca dari file custom (jika ada) atau fallback ke aset bawaan
- **Kembalikan ke Default** menghapus file custom → simulasi berikutnya pakai data aset

---

## 🧮 Logika Simulasi (Identik dengan Tkinter)

Semua fungsi berikut **TIDAK diubah** dari versi Tkinter asli — hanya dipanggil dari UI Kivy:

| Fungsi | Deskripsi |
|---|---|
| `get_poisson_random(mean)` | Knuth Poisson algorithm; pakai normal approximation untuk mean > 30 |
| `generate_fruit_count(min, max, luck)` | Poisson terbobot luck |
| `user_alpha_to_internal(u)` | Mapping -1..1 → 0.001..2.0 (piecewise linear) |
| `kalkulasi_berat_eksponensial(berat_rata, alpha, max_berat)` | Distribusi eksponensial |
| `kalkulasi_harga_dinamis(berat, berat_rata, harga_dasar)` | Multiplier 1 + 1.5 × pct_excess |
| `simulasi_mutasi(alpha, percobaan)` | Roll chance × alpha per buah, break on first hit |
| `simulasi_berkali(plant, iterasi, alpha)` | Pipeline lengkap untuk tanaman panen berkali |
| `simulasi_sekali(plant, iterasi, alpha)` | Pipeline lengkap untuk tanaman panen sekali |

**Catatan**: `simulasi_mutasi` sekarang membaca chance dari `ACTIVE_MUTASI` dan multiplier dari `RARITY_MULTIPLIER` (yang dapat diedit lewat tab Katalog), sehingga editan user langsung berlaku pada simulasi berikutnya.

---

## 🎨 Tema UI

| Token | Hex | Penggunaan |
|---|---|---|
| BG         | `#07090b` | Latar utama |
| BG_MID     | `#0c1014` | Latar input/spinner |
| CARD       | `#101518` | Kartu kontrol |
| CARD2      | `#141b20` | Kartu sekunder |
| BORDER     | `#1e2a33` | Border tipis |
| BORDER_LIT | `#2d4052` | Border hover |
| GREEN      | `#22c55e` | Aksen utama, tombol run |
| GREEN_DIM  | `#16a34a` | Background tombol run |
| AMBER      | `#f59e0b` | Total harga, estimasi panen |
| RED        | `#ef4444` | Alpha negatif, error |
| TEXT       | `#dde4ec` | Teks utama |
| MUTED      | `#546979` | Teks sekunder |
| LABEL_CLR  | `#7fa3bd` | Label field |

Font: **DroidSansMono** (monospasi, tersedia di Android secara default).

---

## 🐛 Troubleshooting

### Build gagal: "SDK license not accepted"
```bash
# Hapus cache buildozer dan ulangi
rm -rf ~/.buildozer
buildozer android debug
# Saat diminta, ketik "y" untuk accept license
```

### Aplikasi crash di Android
Lihat log dengan:
```bash
adb logcat -s python:stdout python:stderr AndroidRuntime
```
Penyebab umum:
- `shop.json` tidak ter-include → cek `source.include_exts` di buildozer.spec (harus ada `json`)
- Permission storage → aplikasi ini tidak butuh permission tambahan (pakai internal storage)

### Data editan hilang setelah uninstall
Ini **normal** — internal storage ikut terhapus saat uninstall. Backup `data/shop_custom.json` & `data/mutasi_custom.json` jika perlu.

### Font monospace tidak muncul
Kivy akan fallback ke font default jika `DroidSansMono` tidak ditemukan di perangkat. Untuk konsistensi, bisa tambahkan file `.ttf` ke folder proyek dan update `FONT_MONO` di main.py.

### Slider cursor terlalu kecil
Edit di KV: `cursor_size: dp(28), dp(28)` — naikkan ke `dp(36), dp(36)` jika masih susah disentuh.

---

## 📋 Spesifikasi Build

| Item | Nilai |
|---|---|
| Package | `org.gachafarm.simulator` |
| minSdk | 24 (Android 7.0) |
| targetSdk | 34 (Android 14) |
| Architecture | arm64-v8a, armeabi-v7a, x86_64 (auto) |
| Orientation | Portrait |
| Permissions | (tidak ada) |
| Bootstrap | SDL2 |
| Python | 3.11+ |
| Kivy | 2.3.0 |

---

## 📝 Lisensi

Aplikasi ini adalah konversi dari kode Python Tkinter milik pengguna. Logika simulasi (distribusi Poisson, algoritma alpha, sistem mutasi) tetap milik pemilik asli.
