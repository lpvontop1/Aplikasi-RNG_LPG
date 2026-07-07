# GachaFarm Simulator — Android APK

Aplikasi Android simulator pertanian gacha dengan sistem mutasi (Shiny, Golden, Frost, dll).

## 📦 Download APK Langsung

File APK siap install ada di folder [`apk/`](./apk/):

```
apk/gachafarm-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

**Cara install:**
1. Transfer file `.apk` ke HP Android
2. Buka file manager, tap APK
3. Allow "Install from unknown sources" jika diminta
4. Tap Install

**Spec APK:**
- Package: `org.gachafarm.gachafarm`
- Version: 1.0.0
- Architecture: arm64-v8a + armeabi-v7a (semua HP Android modern)
- Python: 3.12.10
- Kivy: 2.3.0
- Min Android: 7.0 (API 24)
- Target Android: 13 (API 33)
- NDK: r25b (lebih stabil dari r28c untuk Kivy 2.3.0)
- launchMode: `singleTask` (fix SIGABRT crash)
- Size: ~40MB

---

## 🔧 Bug Fixes Tambahan (Build v2 — SIGABRT Crash Fix)

Selain 10 bug fix di atas, build v2 ini memperbaiki **crash SIGABRT** (`FORTIFY: pthread_mutex_lock called on a destroyed mutex`) yang terjadi di Samsung Galaxy A04s dan device Android 13/14 lainnya:

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 11 | 🔴 CRITICAL | **SIGABRT: pthread_mutex_lock on destroyed mutex** — 4 instance PythonActivity dibuat dalam 21 detik → SDL2 mutex use-after-free | `android.manifest.launch_mode = singleTask` di buildozer.spec (mencegah multiple instance) |
| 12 | 🔴 CRITICAL | `KIVY_GL_BACKEND='gl'` SALAH untuk Android — memaksa OpenGL desktop (tidak ada di Android) → GL context crash | Hapus env var, biarkan Kivy auto-detect GLES2 |
| 13 | 🔴 HIGH | `SDL_GL_CONTEXT_MAJOR/MINOR_VERSION` memicu code path EGL yang tidak didukung di Android | Hapus env var dari main.py dan PythonActivity.java |
| 14 | 🔴 HIGH | NDK r28c FORTIFY level 3 terlalu strict → detect use-after-free SDL2 lama → SIGABRT | Pin NDK ke r25b (FORTIFY lebih lenient) |
| 15 | 🟡 MEDIUM | `_uuidmodule.c: fatal error: 'uuid.h' file not found` — conda env's libuuid incompatible dengan arm | Patch `py3.12_disable_uuid.patch` disable _uuid module (tidak dipakai Kivy) |
| 16 | 🟡 MEDIUM | `bzlib.h not found` saat cross-compile python3 | Tambah `libbz2,liblzma` ke requirements |
| 17 | 🟢 LOW | `SDL_RENDER_DRIVER='software'` dan `SDL_FBCON_ACCEL` no-op di Android (untuk Linux framebuffer) | Hapus env var yang tidak relevan |

---

## 🐛 Bug Fixes di `main.py`

10 bug kritis sudah diperbaiki **TANPA mengubah logika simulasi** (algoritma Poisson, eksponensial, harga dinamis, dan mutasi tetap identik dengan versi Tkinter asli):

| # | Severity | Bug | Fix |
|---|----------|-----|-----|
| 1 | 🔴 CRITICAL | KV parser error: nested class rules `<SimulasiTab>:` & `<KatalogTab>:` di dalam `<GachaTabbedPanel>:` — app tidak bisa start | Dihapus nested rules |
| 2 | 🔴 CRITICAL | `save_all_edits` iterate `plants_list.children` (reverse order) → urutan tanaman terbalik setiap kali simpan | `reversed(plants_list.children)` |
| 3 | 🟡 MEDIUM | `mutasi_list.children` reverse order → JSON inkonsisten | `reversed(mutasi_list.children)` |
| 4 | 🔴 HIGH | `reset_to_default` tidak cleanup `_countdown_event` → countdown stale terus tick | Cancel + clear labels |
| 5 | 🔴 HIGH | Tidak ada `on_pause()` → Android OS kill app saat user switch | `return True` |
| 6 | 🟡 MEDIUM | `Clock.schedule_once(lambda *_: ...scroll_y, 0)` no-op + race condition | Pindah `scroll_y=1.0` ke callback |
| 7 | 🟡 MEDIUM | `MutasiEditCard.collect` error message tidak jelas untuk empty input | Try/except dengan pesan jelas |
| 8 | 🟡 MEDIUM | `selected_plant` tetap referensi dict lama setelah save | Re-find by nama+tier |
| 9 | 🟢 LOW | `on_stop` tidak set `_countdown_event = None` | Ditambahkan |
| 10 | 🟢 LOW | `android.bootstrap` deprecated | Tambah `p4a.bootstrap = sdl2` |

---

## 📁 Struktur Repo

```
.
├── apk/                                # APK siap install
│   └── gachafarm-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
├── gachafarm_kivy/                     # Source code aplikasi
│   ├── main.py                         # Kode utama (bug-fixed)
│   ├── buildozer.spec                  # Konfigurasi build APK
│   ├── shop.json                       # Data tanaman (42 berkali + 68 sekali)
│   ├── requirements.txt                # Dependencies untuk desktop testing
│   └── README.md                       # Dokumentasi aplikasi
├── p4a_patches/                        # Patch python-for-android recipes
│   ├── python3/
│   │   ├── __init__.py                 # Pin ke 3.12.10 + apply grpmodule patch
│   │   └── patches/
│   │       └── py3.12_grpmodule_fix.patch  # Fix grpmodule.c di Android
│   ├── hostpython3/
│   │   └── __init__.py                 # Pin ke 3.12.10 (samakan dengan python3)
│   ├── kivy/
│   │   └── __init__.py                 # CFLAGS relax untuk NDK 28c
│   └── build/
│       └── build.py                    # Skip 'pip install -U pip' (broken resolvelib)
└── build_scripts/
    └── buildozer_watchdog.sh           # Script build dengan detachment penuh
```

---

## 🔨 Build Ulang APK (Opsional)

Jika ingin build sendiri di laptop/PC Linux:

### Persyaratan Sistem
- Linux x86_64 (Debian/Ubuntu)
- ~5GB disk space
- 4GB RAM
- JDK 17 (Temurin recommended)
- Python 3.10+ dengan pip
- Build essentials: `gcc g++ make autoconf automake libtool pkg-config cmake unzip zip`

### Langkah-langkah

1. **Install buildozer:**
   ```bash
   pip install buildozer cython virtualenv
   ```

2. **Clone repo ini:**
   ```bash
   git clone https://github.com/lpvontop1/Aplikasi-RNG_LPG.git
   cd Aplikasi-RNG_LPG/gachafarm_kivy
   ```

3. **Apply p4a patches** (jika build pertama kali, buildozer akan clone p4a ke `.buildozer/android/platform/python-for-android/`):
   ```bash
   # Setelah buildozer pertama kali dijalankan dan gagal, copy patch files:
   cp ../p4a_patches/python3/__init__.py .buildozer/android/platform/python-for-android/pythonforandroid/recipes/python3/
   cp ../p4a_patches/python3/patches/py3.12_grpmodule_fix.patch .buildozer/android/platform/python-for-android/pythonforandroid/recipes/python3/patches/
   cp ../p4a_patches/hostpython3/__init__.py .buildozer/android/platform/python-for-android/pythonforandroid/recipes/hostpython3/
   cp ../p4a_patches/kivy/__init__.py .buildozer/android/platform/python-for-android/pythonforandroid/recipes/kivy/
   cp ../p4a_patches/build/build.py .buildozer/android/platform/python-for-android/pythonforandroid/
   ```

4. **Build APK:**
   ```bash
   # Set environment (sesuaikan JAVA_HOME)
   export JAVA_HOME=/path/to/jdk-17
   export PATH=$JAVA_HOME/bin:$PATH
   export MAKEFLAGS="-j2"

   buildozer android debug
   ```

5. **APK akan muncul di:**
   ```
   bin/gachafarm-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
   ```

### Catatan Build

Build pertama kali butuh **30-60 menit** (download SDK/NDK + compile Python, Kivy, SDL2 dari source). Build berikutnya jauh lebih cepat karena cache.

Jika build gagal dengan error:
- `AC_PROG_LIBTOOL undefined` → install libtool
- `pip._vendor.resolvelib` ImportError → patch build.py (sudah disertakan)
- `incompatible function pointer types` → patch kivy recipe (sudah disertakan)
- `setgrent/getgrent/endgrent undeclared` → apply grpmodule patch (sudah disertakan)
- `python3 should have same version as hostpython3` → patch python3 & hostpython3 recipes ke 3.12.10 (sudah disertakan)

---

## 🎮 Cara Pakai Aplikasi

1. Buka app "GachaFarm Simulator"
2. Tab **Simulasi**: pilih kategori → pilih tanaman → set iterasi & luck → jalankan
3. Tab **Katalog**: edit data tanaman & chance mutasi → Simpan

Aplikasi menyimpan data custom di internal storage Android (`/data/data/org.gachafarm.gachafarm/files/data/`). Tombol "Kembalikan ke Default" akan reset ke data bawaan.
