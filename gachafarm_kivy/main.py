# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║         🌿 GachaFarm Simulator — Kivy (Android)              ║
║  Konversi dari Python Tkinter ke Kivy + Buildozer            ║
║  Semua logika perhitungan IDENTIK dengan versi Tkinter       ║
║  Hanya UI yang diadaptasi untuk layar sentuh Android.        ║
╚══════════════════════════════════════════════════════════════╝

Cara menjalankan (desktop untuk testing):
    python main.py

Cara build APK untuk Android:
    buildozer android debug deploy run
    (lihat README.md untuk detail lengkap)

Struktur file:
    main.py          — kode utama (logika + UI Kivy)
    shop.json        — data bawaan tanaman & mutasi (disertakan dalam APK)
    buildozer.spec   — konfigurasi build Android
"""

# ═══════════════════════════════════════════════════════════════
#  IMPORTS — minimal dependensi (hanya Kivy + pustaka standar)
# ═══════════════════════════════════════════════════════════════

import json
import math
import random
import re
import os
import sys
import threading
from datetime import datetime, timedelta

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty,
    ListProperty, ObjectProperty, DictProperty,
)
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.factory import Factory

# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS — Warna & Font (identik dengan versi Tkinter)
# ═══════════════════════════════════════════════════════════════

BG         = "#07090b"
BG_MID     = "#0c1014"
CARD       = "#101518"
CARD2      = "#141b20"
BORDER     = "#1e2a33"
BORDER_LIT = "#2d4052"
GREEN      = "#22c55e"
GREEN_DIM  = "#16a34a"
AMBER      = "#f59e0b"
RED        = "#ef4444"
TEXT       = "#dde4ec"
MUTED      = "#546979"
LABEL_CLR  = "#7fa3bd"

# Font monospasi — di Android, gunakan "DroidSansMono" atau "DejaVuSansMono"
# Kivy akan fallback ke font default bila tidak ditemukan.
FONT_MONO    = "DroidSansMono"
FONT_MONO_S  = "DroidSansMono"
FONT_HEAD    = "Roboto"

TIER_COLORS = {
    "E": "#94a3b8",
    "D": "#22c55e",
    "C": "#60a5fa",
    "B": "#fbbf24",
    "A": "#f87171",
}

# ═══════════════════════════════════════════════════════════════
#  KONSTANTA MUTASI — Identik dengan versi Tkinter / logic.js
#  Default dipakai saat pertama kali aplikasi dijalankan dan saat
#  user menekan tombol "Kembalikan ke Default".
# ═══════════════════════════════════════════════════════════════

DEFAULT_MUTASI = {
    "Shiny":      0.025,
    "Golden":     0.018,
    "Frost":      0.012,
    "Electrized": 0.008,
    "Inferno":    0.006,
    "Zombified":  0.0045,
    "Rainbow":    0.0025,
    "Invisible":  0.0015,
    "Abyssal":    0.0008,
    "Celestial":  0.0003,
    "Demonic":    0.00015,
    "Angelic":    0.00005,
}

DEFAULT_MULTIPLIER = {
    "Shiny":      1.5,
    "Golden":     2.0,
    "Frost":      2.5,
    "Electrized": 3.0,
    "Inferno":    3.5,
    "Zombified":  4.0,
    "Rainbow":    5.0,
    "Invisible":  6.0,
    "Abyssal":    8.0,
    "Celestial":  12.0,
    "Demonic":    18.0,
    "Angelic":    30.0,
}

RARITY_COLORS = {
    "Shiny":      "#facc15",
    "Golden":     "#fb923c",
    "Frost":      "#67e8f9",
    "Electrized": "#a78bfa",
    "Inferno":    "#f87171",
    "Zombified":  "#4ade80",
    "Rainbow":    "#f472b6",
    "Invisible":  "#e2e8f0",
    "Abyssal":    "#818cf8",
    "Celestial":  "#fde68a",
    "Demonic":    "#ff6b6b",
    "Angelic":    "#bfdbfe",
}

# Multiplier yang aktif (dapat diubah dari editor katalog)
RARITY_MULTIPLIER = dict(DEFAULT_MULTIPLIER)
# Chance yang aktif (dapat diubah dari editor katalog)
ACTIVE_MUTASI     = dict(DEFAULT_MUTASI)


# ═══════════════════════════════════════════════════════════════
#  PARSING DATA SHOP — Identik dengan versi Tkinter
# ═══════════════════════════════════════════════════════════════

def parse_panen_range(s: str) -> dict:
    """'15 - 20 buah' → {min:15, max:20, satuan:'buah'}"""
    m = re.match(r'(\d+)\s*-\s*(\d+)\s*(.+)', s)
    if not m:
        return {"min": 1, "max": 1, "satuan": "unit"}
    return {"min": int(m.group(1)), "max": int(m.group(2)), "satuan": m.group(3).strip()}


def parse_berat_rata_rata(s: str) -> dict:
    """'20 gram / buah' → {valueGram:20, display:'20 gram'}"""
    m = re.match(r'([\d.]+)\s*(gram|kg)\s*/\s*(.+)', s, re.IGNORECASE)
    if not m:
        return {"valueGram": 100, "display": "100 gram"}
    val  = float(m.group(1))
    unit = m.group(2).lower()
    vg   = val * 1000 if unit == "kg" else val
    return {"valueGram": vg, "display": f"{m.group(1)} {m.group(2)}"}


def parse_harga_jual(s: str) -> float:
    """'2 / buah' → 2.0"""
    m = re.search(r'([\d.]+)', s)
    return float(m.group(1)) if m else 1.0


def parse_durasi(s: str) -> float:
    """'7 Jam' → 7.0"""
    m = re.search(r'([\d.]+)', s)
    return float(m.group(1)) if m else 1.0


def parse_hasil_panen(s: str) -> dict:
    """'1 kg' → {valueGram:1000, display:'1 kg'}"""
    m = re.match(r'([\d.]+)\s*(kg|gr|g)\b', s, re.IGNORECASE)
    if not m:
        return {"valueGram": 1000, "display": s}
    val  = float(m.group(1))
    unit = m.group(2).lower()
    vg   = val * 1000 if unit == "kg" else val
    return {"valueGram": vg, "display": s}


def build_plant_info(item: dict, category: str) -> dict:
    """Bangun objek tanaman dari data shop (identik Tkinter)."""
    if category == "berkali":
        panen  = parse_panen_range(item["hasil_panen_range"])
        berat  = parse_berat_rata_rata(item["berat_rata_rata"])
        harga  = parse_harga_jual(item["harga_jual"])
        durasi = parse_durasi(item["durasi"])
        return {
            "nama": item["nama_tanaman"],
            "tier": item["tier"],
            "kategori": "Sekali Tanam, Panen Berkali-kali",
            "durasi": durasi,
            "minBuah": panen["min"],
            "maxBuah": panen["max"],
            "satuan": panen["satuan"],
            "beratRataRataGram": berat["valueGram"],
            "beratDisplay": berat["display"],
            "hargaJual": harga,
            "hargaBibit": item["harga_bibit"],
            "hargaJualStr": item["harga_jual"],
            "isBerkali": True,
            # simpan field mentah agar editor bisa menyimpan ulang
            "_raw": dict(item),
        }
    else:
        hasil  = parse_hasil_panen(item["hasil_panen"])
        durasi = parse_durasi(item["durasi_panen"])
        return {
            "nama": item["nama_tanaman"],
            "tier": item["tier"],
            "kategori": "Sekali Tanam, Sekali Panen",
            "durasi": durasi,
            "hasilPanenGram": hasil["valueGram"],
            "hasilPanenDisplay": hasil["display"],
            "hargaJual": item["harga_jual_lpg"],
            "hargaBibit": item["harga_bibit_lpg"],
            "isBerkali": False,
            "_raw": dict(item),
        }


# ═══════════════════════════════════════════════════════════════
#  ALGORITMA DISTRIBUSI — Identik dengan versi Tkinter
#  TIDAK ADA perubahan pada logika perhitungan.
# ═══════════════════════════════════════════════════════════════

def get_poisson_random(mean: float) -> int:
    """Poisson random (Knuth algorithm) — identik dengan JS."""
    if mean <= 0:
        return 0
    if mean > 30:
        std_dev = math.sqrt(mean)
        result  = mean + std_dev * (
            random.random() + random.random() + random.random() +
            random.random() + random.random() + random.random() - 3
        )
        return max(0, round(result))
    L = math.exp(-mean)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            break
    return k - 1


def generate_fruit_count(min_b: int, max_b: int, luck: float) -> int:
    """Hitung jumlah buah dengan distribusi Poisson terbobot luck."""
    base_mean   = (min_b + max_b) / 2
    extra_boost = (max_b - base_mean) * luck if luck >= 0 else (base_mean - min_b) * luck
    mean_count  = max(0.5, base_mean + extra_boost)
    raw_count   = get_poisson_random(mean_count)
    return max(min_b, min(raw_count, max_b))


def user_alpha_to_internal(u: float) -> float:
    """-1.0→0.001, 0→0.125, +1.0→2.0"""
    if u >= 0:
        return 0.125 + u * 1.875
    else:
        return 0.001 + (u + 1) * 0.124


def alpha_label(u: float) -> str:
    if u <= -0.75: return "Sangat Sulit"
    if u <= -0.25: return "Sulit"
    if u <   0.25: return "Normal"
    if u <   0.75: return "Mudah"
    return "Sangat Mudah"


def alpha_label_color(u: float) -> str:
    if u <= -0.75: return "#ef4444"
    if u <= -0.25: return "#f87171"
    if u <   0.25: return LABEL_CLR
    if u <   0.75: return "#86efac"
    return "#22c55e"


def get_alpha_sublabel(u: float) -> str:
    if u <= -0.75: return "Hampir mustahil dapat mutasi"
    if u <= -0.25: return "Hasil & mutasi di bawah rata-rata"
    if u <   0.25: return "Peluang standar simulator"
    if u <   0.75: return "Hasil & mutasi di atas rata-rata"
    return "Mutasi mudah, hasil maksimal"


def kalkulasi_berat_eksponensial(berat_rata: float, alpha: float, max_berat: float) -> float:
    """Hitung berat buah secara eksponensial — identik dengan JS."""
    scale = berat_rata * alpha
    r     = random.random()
    berat = berat_rata + (-math.log(1 - r + 1e-10) * scale)
    return min(round(berat, 4), max_berat)


def kalkulasi_harga_dinamis(berat: float, berat_rata: float, harga_dasar: float) -> int:
    """Harga dinamis berdasarkan berat relatif terhadap rata-rata."""
    if berat <= berat_rata:
        return int(harga_dasar)
    selisih    = berat - berat_rata
    pct_excess = selisih / berat_rata
    multiplier = 1 + pct_excess * 1.5
    return math.floor(harga_dasar * multiplier)


def simulasi_mutasi(alpha: float, percobaan: int) -> dict:
    """Simulasi mutasi untuk setiap percobaan — pakai chance AKTIF."""
    hasil        = {k: 0 for k in ACTIVE_MUTASI}
    total_mutasi = 0
    details      = []
    for i in range(percobaan):
        found = None
        for nama, chance in ACTIVE_MUTASI.items():
            if random.random() < chance * alpha:
                hasil[nama] += 1
                total_mutasi += 1
                found = nama
                break
        details.append({"no": i + 1, "mutasi": found})
    return {"hasil": hasil, "totalMutasi": total_mutasi, "details": details}


# ═══════════════════════════════════════════════════════════════
#  SIMULASI UTAMA — Identik dengan versi Tkinter
# ═══════════════════════════════════════════════════════════════

def simulasi_berkali(plant: dict, iterasi: int, user_alpha: float) -> dict:
    alpha = user_alpha_to_internal(user_alpha)

    # Step 1: jumlah buah per iterasi
    fruit_count_results = []
    total_fruits = 0
    for i in range(1, iterasi + 1):
        count = generate_fruit_count(plant["minBuah"], plant["maxBuah"], user_alpha)
        fruit_count_results.append({"iterasi": i, "jumlah": count})
        total_fruits += count

    # Step 2: simulasi mutasi (satu cek per buah)
    mutasi_result = simulasi_mutasi(alpha, total_fruits)

    # Step 3: berat & harga setiap buah
    max_berat      = plant["beratRataRataGram"] * 1000
    weight_results = []
    total_berat    = 0
    total_harga    = 0

    for i in range(1, total_fruits + 1):
        berat = kalkulasi_berat_eksponensial(plant["beratRataRataGram"], alpha, max_berat)
        harga = kalkulasi_harga_dinamis(berat, plant["beratRataRataGram"], plant["hargaJual"])

        detail = mutasi_result["details"][i - 1]
        if detail and detail["mutasi"]:
            harga = math.floor(harga * RARITY_MULTIPLIER[detail["mutasi"]])

        weight_results.append({
            "no": i,
            "beratGram": berat,
            "harga": harga,
            "mutasi": detail["mutasi"] if detail else None,
        })
        total_berat += berat
        total_harga += harga

    avg_berat = total_berat / total_fruits if total_fruits > 0 else 0
    avg_harga = total_harga / total_fruits if total_fruits > 0 else 0

    return {
        "userAlpha": user_alpha,
        "alpha": alpha,
        "fruitCountResults": fruit_count_results,
        "totalFruits": total_fruits,
        "mutasiResult": mutasi_result,
        "weightResults": weight_results,
        "totalBeratGram": total_berat,
        "avgBeratGram": avg_berat,
        "totalHarga": total_harga,
        "avgHarga": avg_harga,
    }


def simulasi_sekali(plant: dict, iterasi: int, user_alpha: float) -> dict:
    alpha      = user_alpha_to_internal(user_alpha)
    hasil_gram = plant["hasilPanenGram"]

    mean_yield_factor = 0.5 + (user_alpha + 1) * 0.5
    mean_yield        = hasil_gram * mean_yield_factor

    harvests    = []
    total_harga = 0

    for i in range(1, iterasi + 1):
        scale      = mean_yield * alpha
        r          = random.random()
        aktual     = min(mean_yield + (-math.log(1 - r + 1e-10) * scale), hasil_gram * 5)

        mu_check = simulasi_mutasi(alpha, 1)
        mutasi   = None
        if mu_check["totalMutasi"] > 0:
            for k, v in mu_check["hasil"].items():
                if v > 0:
                    mutasi = k
                    break

        pct_gram = aktual / hasil_gram
        harga    = math.floor(plant["hargaJual"] * pct_gram)
        if mutasi:
            harga = math.floor(harga * RARITY_MULTIPLIER[mutasi])

        harvests.append({
            "no": i,
            "aktualGram": round(aktual, 2),
            "mutasi": mutasi,
            "harga": harga,
        })
        total_harga += harga

    return {
        "userAlpha": user_alpha,
        "alpha": alpha,
        "harvests": harvests,
        "totalHarga": total_harga,
        "avgHarga": total_harga / iterasi,
    }


# ═══════════════════════════════════════════════════════════════
#  FORMAT HELPER — Identik dengan versi Tkinter
# ═══════════════════════════════════════════════════════════════

def format_gram(g: float) -> str:
    if g >= 1000:
        return f"{g / 1000:.3f} kg"
    return f"{g:.2f} gram"


def format_ribuan(n: float) -> str:
    return f"{round(n):,}".replace(",", ".")


def hitung_waktu_panen(dt_str: str, durasi_jam: float):
    try:
        now     = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M")
        selesai = now + timedelta(hours=durasi_jam)
        return selesai
    except Exception:
        return None


def format_datetime_id(d: datetime) -> str:
    if not d:
        return "—"
    DAYS   = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    return f"{DAYS[d.weekday()]}, {d.day:02d} {MONTHS[d.month-1]} {d.year} {d.hour:02d}:{d.minute:02d}"


def format_countdown(selesai: datetime) -> str:
    diff = selesai - datetime.now()
    if diff.total_seconds() <= 0:
        return "Sudah bisa panen!"
    total_s = int(diff.total_seconds())
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    return f"{h}j {m}m {s}d"


# ═══════════════════════════════════════════════════════════════
#  STORAGE HELPER — Internal storage Android + aset APK
# ═══════════════════════════════════════════════════════════════

def get_app_root_dir() -> str:
    """
    Direktori root aplikasi:
      - Android: /data/data/<package>/files  (ANDROID_APP_PATH atau app_data_dir)
      - Desktop: <script_dir>/app_data
    """
    # Kivy / python-for-android menyediakan variabel lingkungan ini
    for env_key in ("ANDROID_APP_PATH", "P4A_APP_PATH"):
        path = os.environ.get(env_key)
        if path and os.path.isdir(path):
            return path
    # python-for-android: SDL_AndroidGetInternalStoragePath
    # biasanya env vars di pythonactivity:
    if hasattr(sys, "android_api_version") or "ANDROID_DATA" in os.environ:
        # coba pakai folder files dari PRIVATE storage
        try:
            from android.storage import app_storage_path  # type: ignore
            p = app_storage_path()
            if p and os.path.isdir(p):
                return p
        except Exception:
            pass
    # Fallback desktop
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_data")


def get_data_dir() -> str:
    """Direktori data internal (data/shop_custom.json)."""
    d = os.path.join(get_app_root_dir(), "data")
    os.makedirs(d, exist_ok=True)
    return d


def get_custom_shop_path() -> str:
    return os.path.join(get_data_dir(), "shop_custom.json")


def get_custom_mutasi_path() -> str:
    return os.path.join(get_data_dir(), "mutasi_custom.json")


def get_asset_shop_path() -> str:
    """
    Path ke shop.json bawaan (aset yang disertakan dalam APK via buildozer.spec).
    Pada Android, aset diakses melalui app_directory dari AAR.
    """
    # di python-for-android, file yang di-include via source.include_exts
    # berada di /data/data/<pkg>/files/_python_bundle/_python_bundle/
    # atau bisa diakses via os.path.dirname(__file__) bila main.py di-repack.
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.json"),
        os.path.join(get_app_root_dir(), "shop.json"),
    ]
    # tambah path khusus python-for-android
    try:
        # coba via android module
        from android.storage import app_storage_path  # type: ignore
        candidates.append(os.path.join(app_storage_path(), "shop.json"))
    except Exception:
        pass
    for p in candidates:
        if os.path.exists(p):
            return p
    # default — biarkan load_default_shop_data melempar FileNotFoundError
    return candidates[0]


def load_default_shop_data() -> dict:
    """Baca shop.json bawaan dari aset APK."""
    path = get_asset_shop_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            "shop.json tidak ditemukan di aset APK!\n"
            "Pastikan shop.json disertakan via buildozer.spec (source.include_exts)."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_shop_data() -> dict:
    """
    Muat data tanaman:
      1. shop_custom.json (jika ada di internal storage)
      2. fallback ke shop.json bawaan (aset APK)
    """
    custom_path = get_custom_shop_path()
    if os.path.exists(custom_path):
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # korup — fallback ke default
            pass
    return load_default_shop_data()


def save_shop_data(data: dict) -> None:
    """Simpan data tanaman hasil edit ke internal storage."""
    custom_path = get_custom_shop_path()
    with open(custom_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_mutasi_data() -> dict:
    """
    Muat data mutasi (chance + multiplier) dari internal storage.
    Return: {"chance": {...}, "multiplier": {...}}
    """
    custom_path = get_custom_mutasi_path()
    if os.path.exists(custom_path):
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            chance     = d.get("chance", dict(DEFAULT_MUTASI))
            multiplier = d.get("multiplier", dict(DEFAULT_MULTIPLIER))
            return {"chance": chance, "multiplier": multiplier}
        except (json.JSONDecodeError, OSError):
            pass
    return {"chance": dict(DEFAULT_MUTASI), "multiplier": dict(DEFAULT_MULTIPLIER)}


def save_mutasi_data(chance: dict, multiplier: dict) -> None:
    """Simpan data mutasi hasil edit ke internal storage."""
    custom_path = get_custom_mutasi_path()
    payload = {"chance": chance, "multiplier": multiplier}
    with open(custom_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def reset_all_to_default() -> tuple:
    """
    Hapus file custom (shop_custom.json & mutasi_custom.json).
    Return tuple (shop_data, mutasi_data) yang merupakan nilai default.
    """
    for p in (get_custom_shop_path(), get_custom_mutasi_path()):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
    return load_default_shop_data(), {
        "chance": dict(DEFAULT_MUTASI),
        "multiplier": dict(DEFAULT_MULTIPLIER),
    }


def init_active_mutasi():
    """Sinkronkan ACTIVE_MUTASI & RARITY_MULTIPLIER dari storage (dipanggil saat startup)."""
    global ACTIVE_MUTASI, RARITY_MULTIPLIER
    data = load_mutasi_data()
    ACTIVE_MUTASI     = dict(DEFAULT_MUTASI)
    RARITY_MULTIPLIER = dict(DEFAULT_MULTIPLIER)
    for k in DEFAULT_MUTASI:
        if k in data["chance"]:
            ACTIVE_MUTASI[k] = data["chance"][k]
        if k in data["multiplier"]:
            RARITY_MULTIPLIER[k] = data["multiplier"][k]


# ═══════════════════════════════════════════════════════════════
#  KV UI DEFINITION — Dark theme, green accent, monospace font
#  Adaptasi mobile: ScrollView vertikal, tombol besar, Slider,
#  Spinner, TextInput responsif.
# ═══════════════════════════════════════════════════════════════

KV = r"""
#:set BG         "#07090b"
#:set BG_MID     "#0c1014"
#:set CARD       "#101518"
#:set CARD2      "#141b20"
#:set BORDER     "#1e2a33"
#:set BORDER_LIT "#2d4052"
#:set GREEN      "#22c55e"
#:set GREEN_DIM  "#16a34a"
#:set AMBER      "#f59e0b"
#:set RED        "#ef4444"
#:set TEXT       "#dde4ec"
#:set MUTED      "#546979"
#:set LABEL_CLR  "#7fa3bd"
#:set FONT_MONO  "DroidSansMono"

<GachaTabbedPanel>:
    do_default_tab: False
    tab_pos: "top_mid"
    tab_width: Window.width / 2
    tab_height: dp(48)
    background_color: BG_MID

# ────────────────────────────────────────────────────────────────
#  SIMULASI TAB
# ────────────────────────────────────────────────────────────────
<SimulasiTab>:
    text: "Simulasi"
    BoxLayout:
        orientation: "vertical"
        size_hint_y: 1
        ScrollView:
            id: sim_scroll
            do_scroll_x: False
            bar_color: BORDER_LIT
            bar_inactive_color: BORDER
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: dp(12)

                # ═══ HEADER CARD ═══
                BoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: dp(56)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.063, 0.094, 0.117, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "GachaFarm  SIMULATOR"
                        color: TEXT
                        font_name: FONT_MONO
                        font_size: sp(16)
                        bold: True
                        size_hint_x: 0.7
                    Label:
                        id: badge_lbl
                        text: "Kivy Android"
                        color: GREEN
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_x: 0.3
                        halign: "right"

                # ═══ KATEGORI ═══
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(82)
                    padding: dp(12)
                    spacing: dp(4)
                    canvas.before:
                        Color:
                            rgba: 0.063, 0.082, 0.094, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "LANGKAH 1 — KATEGORI TANAMAN"
                        color: LABEL_CLR
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_y: None
                        height: dp(18)
                    Spinner:
                        id: cat_spinner
                        text: "Pilih kategori"
                        values: ["Sekali Tanam, Panen Berkali-kali", "Sekali Tanam, Sekali Panen"]
                        background_color: 0, 0, 0, 0
                        color: TEXT
                        font_name: FONT_MONO
                        font_size: sp(14)
                        size_hint_y: None
                        height: dp(44)
                        canvas.before:
                            Color:
                                rgba: 0.047, 0.063, 0.078, 1
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(4)]
                            Color:
                                rgba: 0.176, 0.251, 0.322, 1
                            Line:
                                width: 1
                                rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)

                # ═══ TANAMAN ═══
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(82)
                    padding: dp(12)
                    spacing: dp(4)
                    canvas.before:
                        Color:
                            rgba: 0.063, 0.082, 0.094, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "LANGKAH 2 — PILIH TANAMAN"
                        color: LABEL_CLR
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_y: None
                        height: dp(18)
                    Spinner:
                        id: plant_spinner
                        text: "Pilih kategori dulu"
                        values: []
                        disabled: True
                        background_color: 0, 0, 0, 0
                        color: TEXT
                        font_name: FONT_MONO
                        font_size: sp(14)
                        size_hint_y: None
                        height: dp(44)
                        canvas.before:
                            Color:
                                rgba: 0.047, 0.063, 0.078, 1
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(4)]
                            Color:
                                rgba: 0.176, 0.251, 0.322, 1
                            Line:
                                width: 1
                                rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)

                # ═══ PREVIEW CARD ═══
                BoxLayout:
                    id: preview_container
                    orientation: "vertical"
                    size_hint_y: None
                    height: 0
                    padding: dp(0)
                    spacing: dp(0)

                # ═══ WAKTU TANAM ═══
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(140)
                    padding: dp(12)
                    spacing: dp(4)
                    canvas.before:
                        Color:
                            rgba: 0.063, 0.082, 0.094, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "LANGKAH 3 — WAKTU TANAM (opsional)"
                        color: LABEL_CLR
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_y: None
                        height: dp(18)
                    TextInput:
                        id: dt_input
                        text: ""
                        multiline: False
                        font_name: FONT_MONO
                        font_size: sp(14)
                        size_hint_y: None
                        height: dp(44)
                        padding: [dp(10), dp(12)]
                        background_color: 0, 0, 0, 0
                        foreground_color: TEXT
                        cursor_color: GREEN
                        canvas.before:
                            Color:
                                rgba: 0.047, 0.063, 0.078, 1
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(4)]
                            Color:
                                rgba: 0.176, 0.251, 0.322, 1
                            Line:
                                width: 1
                                rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)
                    Label:
                        text: "Format: YYYY-MM-DD HH:MM"
                        color: MUTED
                        font_name: FONT_MONO
                        font_size: sp(9)
                        size_hint_y: None
                        height: dp(14)
                    Label:
                        id: harvest_lbl
                        text: ""
                        color: AMBER
                        font_name: FONT_MONO
                        font_size: sp(11)
                        size_hint_y: None
                        height: dp(16)
                    Label:
                        id: countdown_lbl
                        text: ""
                        color: GREEN
                        font_name: FONT_MONO
                        font_size: sp(16)
                        bold: True
                        size_hint_y: None
                        height: dp(22)

                # ═══ ITERASI ═══
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(82)
                    padding: dp(12)
                    spacing: dp(4)
                    canvas.before:
                        Color:
                            rgba: 0.063, 0.082, 0.094, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "LANGKAH 4 — JUMLAH ITERASI / SIKLUS PANEN"
                        color: LABEL_CLR
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_y: None
                        height: dp(18)
                    TextInput:
                        id: iter_input
                        text: "10"
                        multiline: False
                        input_filter: "int"
                        font_name: FONT_MONO
                        font_size: sp(18)
                        bold: True
                        halign: "center"
                        size_hint_y: None
                        height: dp(44)
                        padding: [dp(10), dp(10)]
                        background_color: 0, 0, 0, 0
                        foreground_color: TEXT
                        cursor_color: GREEN
                        canvas.before:
                            Color:
                                rgba: 0.047, 0.063, 0.078, 1
                            RoundedRectangle:
                                pos: self.pos
                                size: self.size
                                radius: [dp(4)]
                            Color:
                                rgba: 0.176, 0.251, 0.322, 1
                            Line:
                                width: 1
                                rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)

                # ═══ LUCK SLIDER ═══
                BoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(180)
                    padding: dp(12)
                    spacing: dp(6)
                    canvas.before:
                        Color:
                            rgba: 0.078, 0.106, 0.125, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "TINGKAT KEBERUNTUNGAN (LUCK)"
                        color: LABEL_CLR
                        font_name: FONT_MONO
                        font_size: sp(11)
                        bold: True
                        size_hint_y: None
                        height: dp(18)
                    BoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(60)
                        Label:
                            id: alpha_big
                            text: "+0.00"
                            color: LABEL_CLR
                            font_name: FONT_MONO
                            font_size: sp(34)
                            bold: True
                            size_hint_x: 0.4
                        BoxLayout:
                            orientation: "vertical"
                            size_hint_x: 0.6
                            Label:
                                id: alpha_name
                                text: "Normal"
                                color: LABEL_CLR
                                font_name: FONT_MONO
                                font_size: sp(13)
                                bold: True
                                halign: "left"
                            Label:
                                id: alpha_sub
                                text: "Peluang standar simulator"
                                color: MUTED
                                font_name: FONT_MONO
                                font_size: sp(9)
                                halign: "left"
                                text_size: self.size
                    BoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(48)
                        Label:
                            text: "-1.0"
                            color: RED
                            font_name: FONT_MONO
                            font_size: sp(10)
                            bold: True
                            size_hint_x: 0.1
                        Slider:
                            id: alpha_slider
                            min: -100
                            max: 100
                            value: 0
                            step: 1
                            size_hint_x: 0.8
                            cursor_size: dp(28), dp(28)
                        Label:
                            text: "+1.0"
                            color: GREEN
                            font_name: FONT_MONO
                            font_size: sp(10)
                            bold: True
                            size_hint_x: 0.1
                    BoxLayout:
                        orientation: "horizontal"
                        size_hint_y: None
                        height: dp(14)
                        Label:
                            text: "-1.0"
                            color: MUTED
                            font_name: FONT_MONO
                            font_size: sp(8)
                            size_hint_x: 0.2
                        Label:
                            text: "-0.5"
                            color: MUTED
                            font_name: FONT_MONO
                            font_size: sp(8)
                            size_hint_x: 0.2
                        Label:
                            text: "0"
                            color: MUTED
                            font_name: FONT_MONO
                            font_size: sp(8)
                            size_hint_x: 0.2
                        Label:
                            text: "+0.5"
                            color: MUTED
                            font_name: FONT_MONO
                            font_size: sp(8)
                            size_hint_x: 0.2
                        Label:
                            text: "+1.0"
                            color: MUTED
                            font_name: FONT_MONO
                            font_size: sp(8)
                            size_hint_x: 0.2

                # ═══ TOMBOL ═══
                Button:
                    id: run_btn
                    text: "JALANKAN SIMULASI"
                    color: 0, 0, 0, 1
                    font_name: FONT_MONO
                    font_size: sp(14)
                    bold: True
                    size_hint_y: None
                    height: dp(56)
                    background_color: 0, 0, 0, 0
                    canvas.before:
                        Color:
                            rgba: 0.086, 0.639, 0.369, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    on_release: app.run_simulation()
                Button:
                    text: "RESET SEMUA"
                    color: MUTED
                    font_name: FONT_MONO
                    font_size: sp(12)
                    size_hint_y: None
                    height: dp(44)
                    background_color: 0, 0, 0, 0
                    canvas.before:
                        Color:
                            rgba: 0.078, 0.106, 0.125, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    on_release: app.reset_all()

                # ═══ HASIL SIMULASI ═══
                BoxLayout:
                    id: results_container
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(8)

                # placeholder saat belum ada hasil
                BoxLayout:
                    id: results_placeholder
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(200)
                    padding: dp(20)
                    canvas.before:
                        Color:
                            rgba: 0.027, 0.035, 0.043, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(6)]
                    Label:
                        text: "Pilih tanaman dan jalankan simulasi\nuntuk melihat hasil di sini"
                        color: MUTED
                        font_name: FONT_MONO
                        font_size: sp(12)
                        halign: "center"
                        markup: True

# ────────────────────────────────────────────────────────────────
#  KATALOG TAB
# ────────────────────────────────────────────────────────────────
<KatalogTab>:
    text: "Katalog"
    BoxLayout:
        orientation: "vertical"
        # tombol toolbar
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(56)
            spacing: dp(6)
            padding: [dp(8), dp(8)]
            canvas.before:
                Color:
                    rgba: 0.039, 0.051, 0.063, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "SIMPAN"
                color: 0, 0, 0, 1
                font_name: FONT_MONO
                font_size: sp(13)
                bold: True
                size_hint_x: 0.5
                background_color: 0, 0, 0, 0
                canvas.before:
                    Color:
                        rgba: 0.086, 0.639, 0.369, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(6)]
                on_release: app.save_all_edits()
            Button:
                text: "KEMBALIKAN KE DEFAULT"
                color: AMBER
                font_name: FONT_MONO
                font_size: sp(12)
                bold: True
                size_hint_x: 0.5
                background_color: 0, 0, 0, 0
                canvas.before:
                    Color:
                        rgba: 0.078, 0.106, 0.125, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(6)]
                    Color:
                        rgba: 0.961, 0.620, 0.043, 0.6
                    Line:
                        width: 1
                        rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(6)
                on_release: app.reset_to_default()

        # sub-tab: Tanaman / Mutasi
        TabbedPanel:
            do_default_tab: False
            tab_pos: "top_mid"
            tab_width: Window.width / 2
            tab_height: dp(44)
            TabbedPanelItem:
                text: "Tanaman"
                ScrollView:
                    do_scroll_x: False
                    bar_color: BORDER_LIT
                    bar_inactive_color: BORDER
                    BoxLayout:
                        id: plants_list
                        orientation: "vertical"
                        size_hint_y: None
                        height: self.minimum_height
                        padding: dp(8)
                        spacing: dp(6)
            TabbedPanelItem:
                text: "Mutasi"
                ScrollView:
                    do_scroll_x: False
                    bar_color: BORDER_LIT
                    bar_inactive_color: BORDER
                    BoxLayout:
                        id: mutasi_list
                        orientation: "vertical"
                        size_hint_y: None
                        height: self.minimum_height
                        padding: dp(8)
                        spacing: dp(6)

# ────────────────────────────────────────────────────────────────
#  WIDGET CARD — KARTU TANAMAN DENGAN INPUT EDITABLE
# ────────────────────────────────────────────────────────────────
<PlantEditCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 0.063, 0.082, 0.094, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]
        Color:
            rgba: tuple(app.hex_to_rgba(root.accent_color))
        RoundedRectangle:
            pos: self.pos[0], self.pos[1]
            size: dp(4), self.size[1]
    Label:
        text: root.title_text
        color: TEXT
        font_name: FONT_MONO
        font_size: sp(13)
        bold: True
        size_hint_y: None
        height: dp(20)
        halign: "left"
        text_size: self.size
    Label:
        text: root.subtitle_text
        color: MUTED
        font_name: FONT_MONO
        font_size: sp(9)
        size_hint_y: None
        height: dp(14)
        halign: "left"
        text_size: self.size
    GridLayout:
        id: fields_grid
        cols: 2
        size_hint_y: None
        height: self.minimum_height
        spacing: dp(4)
        padding: [0, dp(4)]

<FieldRow@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(58)
    padding: [dp(4), dp(2)]
    Label:
        id: field_label
        text: ""
        color: LABEL_CLR
        font_name: FONT_MONO
        font_size: sp(9)
        bold: True
        size_hint_y: None
        height: dp(14)
        halign: "left"
        text_size: self.size
    TextInput:
        id: field_input
        text: ""
        multiline: False
        font_name: FONT_MONO
        font_size: sp(12)
        size_hint_y: None
        height: dp(40)
        padding: [dp(8), dp(8)]
        background_color: 0, 0, 0, 0
        foreground_color: TEXT
        cursor_color: GREEN
        canvas.before:
            Color:
                rgba: 0.047, 0.063, 0.078, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(4)]
            Color:
                rgba: 0.176, 0.251, 0.322, 1
            Line:
                width: 1
                rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)

# ────────────────────────────────────────────────────────────────
#  WIDGET CARD — KARTU MUTASI DENGAN INPUT EDITABLE
# ────────────────────────────────────────────────────────────────
<MutasiEditCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(140)
    padding: dp(10)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: 0.063, 0.082, 0.094, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]
        Color:
            rgba: tuple(app.hex_to_rgba(root.accent_color))
        RoundedRectangle:
            pos: self.pos[0], self.pos[1]
            size: dp(4), self.size[1]
    BoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(24)
        Label:
            text: root.mutasi_name
            color: root.accent_color
            font_name: FONT_MONO
            font_size: sp(15)
            bold: True
            size_hint_x: 0.6
            halign: "left"
            text_size: self.size
        Label:
            text: root.rarity_label
            color: MUTED
            font_name: FONT_MONO
            font_size: sp(9)
            size_hint_x: 0.4
            halign: "right"
            text_size: self.size
    BoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(50)
        spacing: dp(6)
        BoxLayout:
            orientation: "vertical"
            size_hint_x: 0.5
            Label:
                text: "CHANCE (0 - 1)"
                color: LABEL_CLR
                font_name: FONT_MONO
                font_size: sp(9)
                bold: True
                size_hint_y: None
                height: dp(14)
                halign: "left"
                text_size: self.size
            TextInput:
                id: chance_input
                text: ""
                multiline: False
                font_name: FONT_MONO
                font_size: sp(14)
                size_hint_y: None
                height: dp(36)
                padding: [dp(8), dp(8)]
                background_color: 0, 0, 0, 0
                foreground_color: AMBER
                cursor_color: GREEN
                canvas.before:
                    Color:
                        rgba: 0.047, 0.063, 0.078, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(4)]
                    Color:
                        rgba: 0.176, 0.251, 0.322, 1
                    Line:
                        width: 1
                        rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)
        BoxLayout:
            orientation: "vertical"
            size_hint_x: 0.5
            Label:
                text: "MULTIPLIER (x)"
                color: LABEL_CLR
                font_name: FONT_MONO
                font_size: sp(9)
                bold: True
                size_hint_y: None
                height: dp(14)
                halign: "left"
                text_size: self.size
            TextInput:
                id: mult_input
                text: ""
                multiline: False
                font_name: FONT_MONO
                font_size: sp(14)
                size_hint_y: None
                height: dp(36)
                padding: [dp(8), dp(8)]
                background_color: 0, 0, 0, 0
                foreground_color: GREEN
                cursor_color: GREEN
                canvas.before:
                    Color:
                        rgba: 0.047, 0.063, 0.078, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(4)]
                    Color:
                        rgba: 0.176, 0.251, 0.322, 1
                    Line:
                        width: 1
                        rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(4)
    Label:
        text: root.hint_text
        color: MUTED
        font_name: FONT_MONO
        font_size: sp(8)
        size_hint_y: None
        height: dp(14)
        halign: "left"
        text_size: self.size

# ────────────────────────────────────────────────────────────────
#  WIDGET UNTUK MENAMPILKAN BARIS TABEL HASIL SIMULASI
# ────────────────────────────────────────────────────────────────
<StatsCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 0.063, 0.082, 0.094, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]
        Color:
            rgba: 0.086, 0.639, 0.369, 1
        RoundedRectangle:
            pos: self.pos[0], self.pos[1]
            size: dp(4), self.size[1]
    Label:
        text: root.card_title
        color: TEXT
        font_name: FONT_MONO
        font_size: sp(12)
        bold: True
        size_hint_y: None
        height: dp(20)
        halign: "left"
        text_size: self.size
    GridLayout:
        id: stats_grid
        cols: root.grid_cols
        size_hint_y: None
        height: self.minimum_height
        spacing: dp(4)
        padding: [0, dp(2)]

<StatCell@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(54)
    padding: [dp(6), dp(4)]
    canvas.before:
        Color:
            rgba: 0.027, 0.035, 0.043, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]
    Label:
        text: ctx_label
        color: LABEL_CLR
        font_name: FONT_MONO
        font_size: sp(8)
        bold: True
        size_hint_y: None
        height: dp(14)
        halign: "left"
        text_size: self.size
    Label:
        text: ctx_value
        color: ctx_color
        font_name: FONT_MONO
        font_size: sp(13)
        bold: True
        size_hint_y: None
        height: dp(20)
        halign: "left"
        text_size: self.size

<GrandTotalCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(160)
    padding: dp(20)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: 0.051, 0.122, 0.051, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6)]
        Color:
            rgba: 0.086, 0.639, 0.369, 1
        Line:
            width: 2
            rounded_rectangle: self.pos[0], self.pos[1], self.size[0], self.size[1], dp(6)
    Label:
        text: "GRAND TOTAL"
        color: GREEN
        font_name: FONT_MONO
        font_size: sp(11)
        bold: True
        size_hint_y: None
        height: dp(18)
    Label:
        text: root.total_text
        color: AMBER
        font_name: FONT_MONO
        font_size: sp(28)
        bold: True
        size_hint_y: None
        height: dp(40)
    Label:
        text: root.sub_text
        color: MUTED
        font_name: FONT_MONO
        font_size: sp(9)
        size_hint_y: None
        height: dp(16)

<TableHeader@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(28)
    canvas.before:
        Color:
            rgba: 0.078, 0.106, 0.125, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4), dp(4), 0, 0]

<TableHeaderCell@Label>:
    color: LABEL_CLR
    font_name: FONT_MONO
    font_size: sp(10)
    bold: True
    canvas.before:
        Color:
            rgba: 0.078, 0.106, 0.125, 1
        Rectangle:
            pos: self.pos
            size: self.size

<TableLine@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(26)

<TableLineCell@Label>:
    color: TEXT
    font_name: FONT_MONO
    font_size: sp(10)
    canvas.before:
        Color:
            rgba: 0.047, 0.063, 0.078, 1
        Rectangle:
            pos: self.pos
            size: self.size
"""


# ═══════════════════════════════════════════════════════════════
#  WIDGET CLASSES — Custom widgets for plant/mutasi editor
# ═══════════════════════════════════════════════════════════════

class GachaTabbedPanel(TabbedPanel):
    """Root TabbedPanel dengan dua tab: Simulasi & Katalog."""
    pass


class SimulasiTab(TabbedPanelItem):
    """Tab Simulasi — kontrol + hasil."""
    pass


class KatalogTab(TabbedPanelItem):
    """Tab Katalog — editor tanaman & mutasi."""
    pass


class PlantEditCard(BoxLayout):
    """Kartu editor untuk satu tanaman — berisi TextInput field-field."""
    title_text    = StringProperty("")
    subtitle_text = StringProperty("")
    accent_color  = StringProperty(LABEL_CLR)
    # list berisi tuple (label, field_name, value_str) — diisi dari Python
    fields        = ListProperty([])
    # reference ke plant dict asli
    plant_raw     = DictProperty({})
    category      = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self._build_fields, 0)

    def _build_fields(self, *_):
        grid = self.ids.fields_grid
        grid.clear_widgets()
        for label, field, value in self.fields:
            # Gunakan Factory.FieldRow (didefinisikan di KV string global)
            row = Factory.FieldRow()
            row.ids.field_label.text = label
            row.ids.field_input.text = str(value)
            row.ids.field_input.field_name = field  # type: ignore[attr-defined]
            grid.add_widget(row)

    def collect_values(self) -> dict:
        """Ambil nilai dari semua TextInput → {field_name: str_value}."""
        out = {}
        for row in self.ids.fields_grid.children:
            ti = row.ids.field_input
            out[ti.field_name] = ti.text  # type: ignore[attr-defined]
        return out


class MutasiEditCard(BoxLayout):
    """Kartu editor untuk satu mutasi (chance + multiplier)."""
    mutasi_name   = StringProperty("")
    accent_color  = StringProperty(LABEL_CLR)
    rarity_label  = StringProperty("")
    hint_text     = StringProperty("")
    chance_value  = StringProperty("")
    mult_value    = StringProperty("")

    def collect(self) -> tuple:
        """Return (chance_float, multiplier_float) — raise ValueError jika invalid."""
        try:
            chance = float(self.ids.chance_input.text.strip())
            mult   = float(self.ids.mult_input.text.strip())
        except ValueError:
            raise ValueError(
                f"{self.mutasi_name}: input harus angka valid "
                f"(chance='{self.ids.chance_input.text}', "
                f"mult='{self.ids.mult_input.text}')"
            )
        if not (0.0 <= chance <= 1.0):
            raise ValueError(f"Chance {self.mutasi_name} harus 0..1 (dapat: {chance})")
        if mult <= 0:
            raise ValueError(f"Multiplier {self.mutasi_name} harus > 0 (dapat: {mult})")
        return chance, mult


class StatsCard(BoxLayout):
    """Kartu statistik dengan grid 2/3/4 kolom."""
    card_title = StringProperty("")
    grid_cols  = NumericProperty(4)


class GrandTotalCard(BoxLayout):
    """Kartu grand total di akhir hasil simulasi."""
    total_text = StringProperty("")
    sub_text   = StringProperty("")


def _make_card_bg(widget, bg_rgba, accent_rgba=None, radius=6):
    """
    Tambahkan background + accent bar ke widget, dengan auto-update
    saat widget di-resize / di-reposition oleh parent layout.
    """
    bg_col  = Color(*bg_rgba)
    bg_rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    accent_col  = None
    accent_rect = None
    if accent_rgba:
        accent_col  = Color(*accent_rgba)
        accent_rect = RoundedRectangle(pos=(widget.pos[0], widget.pos[1]),
                                       size=(dp(4), widget.size[1]))

    widget.canvas.before.add(bg_col)
    widget.canvas.before.add(bg_rect)
    if accent_rgba:
        widget.canvas.before.add(accent_col)
        widget.canvas.before.add(accent_rect)

    def _update(inst, val):
        bg_rect.pos = inst.pos
        bg_rect.size = inst.size
        if accent_rect:
            accent_rect.pos = (inst.pos[0], inst.pos[1])
            accent_rect.size = (dp(4), inst.size[1])

    widget.bind(pos=_update, size=_update)
    return widget


def _make_cell_bg(widget, bg_rgba, radius=4):
    """Tambahkan background cell dengan auto-update pos/size."""
    bg_col  = Color(*bg_rgba)
    bg_rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    widget.canvas.before.add(bg_col)
    widget.canvas.before.add(bg_rect)

    def _update(inst, val):
        bg_rect.pos = inst.pos
        bg_rect.size = inst.size

    widget.bind(pos=_update, size=_update)
    return widget


def _make_label_bg(widget, bg_rgba):
    """Tambahkan background Rectangle ke Label dengan auto-update."""
    bg_col  = Color(*bg_rgba)
    bg_rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.canvas.before.add(bg_col)
    widget.canvas.before.add(bg_rect)

    def _update(inst, val):
        bg_rect.pos = inst.pos
        bg_rect.size = inst.size

    widget.bind(pos=_update, size=_update)
    return widget


# ═══════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════

class GachaFarmApp(App):
    """
    Aplikasi GachaFarm — Kivy untuk Android.
    Mengelola: data tanaman, data mutasi, simulasi, editor katalog,
    loading indicator (Thread + Clock), error handling via Popup.
    """

    # ── State ──────────────────────────────────────────────────
    plants_berkali     = ListProperty([])
    plants_sekali      = ListProperty([])
    current_category   = StringProperty("")    # "berkali" / "sekali"
    current_plants     = ListProperty([])
    selected_plant     = ObjectProperty(allownone=True)
    harvest_time       = ObjectProperty(allownone=True)
    is_simulating      = BooleanProperty(False)

    # Countdown scheduling
    _countdown_event   = None

    # ── Build ──────────────────────────────────────────────────
    def build(self):
        # Inisialisasi: muat chance/multiplier dari storage
        try:
            init_active_mutasi()
        except Exception as e:
            print("[WARN] init_active_mutasi gagal:", e)

        # Muat data shop
        try:
            raw = load_shop_data()
        except FileNotFoundError as err:
            self._show_error("Data Tidak Ditemukan", str(err))
            raw = {"tanaman_sekali_tanam_panen_berkali_kali": [],
                   "tanaman_sekali_tanam_sekali_panen": []}

        self._raw_shop = raw
        self.plants_berkali = [build_plant_info(i, "berkali")
                               for i in raw.get("tanaman_sekali_tanam_panen_berkali_kali", [])]
        self.plants_sekali  = [build_plant_info(i, "sekali")
                               for i in raw.get("tanaman_sekali_tanam_sekali_panen", [])]

        # Build UI
        Builder.load_string(KV)
        self.root_panel = GachaTabbedPanel()

        # Tab Simulasi
        self.sim_tab = SimulasiTab(text="Simulasi")
        self.root_panel.add_widget(self.sim_tab)

        # Tab Katalog
        self.katalog_tab = KatalogTab(text="Katalog")
        self.root_panel.add_widget(self.katalog_tab)

        # Set default tab
        self.root_panel.default_tab = self.sim_tab

        # Bind events after UI built
        Clock.schedule_once(self._post_build, 0)

        return self.root_panel

    def _post_build(self, *_):
        """Init setelah UI selesai dibuild."""
        # Set datetime default
        sim = self.sim_tab
        sim.ids.dt_input.text = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Bind events
        sim.ids.cat_spinner.bind(text=self._on_category_change)
        sim.ids.plant_spinner.bind(text=self._on_plant_change)
        sim.ids.alpha_slider.bind(value=self._on_alpha_change)

        # Bind dt_input untuk update harvest time
        sim.ids.dt_input.bind(text=self._on_dt_change)

        # Initial alpha display
        self._on_alpha_change(sim.ids.alpha_slider, 0)

        # Build katalog editor
        self._build_katalog_editor()

    # ── Helper: hex → rgba tuple ──────────────────────────────
    @staticmethod
    def hex_to_rgba(hex_str: str) -> tuple:
        """Convert '#22c55e' → (0.133, 0.773, 0.369, 1.0)"""
        s = hex_str.lstrip("#")
        if len(s) == 3:
            s = "".join([c * 2 for c in s])
        try:
            r = int(s[0:2], 16) / 255.0
            g = int(s[2:4], 16) / 255.0
            b = int(s[4:6], 16) / 255.0
        except ValueError:
            return (0.5, 0.5, 0.5, 1.0)
        return (r, g, b, 1.0)

    # ── Event handlers: Simulasi ──────────────────────────────
    def _on_category_change(self, spinner, text):
        if not text or text == "Pilih kategori":
            return
        if "Berkali" in text:
            self.current_category = "berkali"
            self.current_plants   = self.plants_berkali
        else:
            self.current_category = "sekali"
            self.current_plants   = self.plants_sekali

        plant_spinner = self.sim_tab.ids.plant_spinner
        plant_spinner.disabled = False
        plant_spinner.values = [f"[{p['tier']}] {p['nama']}" for p in self.current_plants]
        plant_spinner.text = "Pilih tanaman"
        self.selected_plant = None
        self._hide_preview()

    def _on_plant_change(self, spinner, text):
        if not text or text == "Pilih tanaman":
            return
        # cari plant berdasarkan nama
        try:
            # format: "[E] Abelmoschus (Okra)"
            tier = text[1:text.index("]")]
            nama = text[text.index("]") + 2:].strip()
            for p in self.current_plants:
                if p["nama"] == nama and p["tier"] == tier:
                    self.selected_plant = p
                    break
        except (ValueError, IndexError):
            return
        if self.selected_plant:
            self._render_plant_preview(self.selected_plant)
            self._update_harvest_time()

    def _on_dt_change(self, *_):
        self._update_harvest_time()

    def _on_alpha_change(self, slider, value):
        u     = float(value) / 100.0
        u_str = f"+{u:.2f}" if u >= 0 else f"{u:.2f}"
        col   = alpha_label_color(u)
        sim   = self.sim_tab
        sim.ids.alpha_big.text  = u_str
        sim.ids.alpha_big.color = self.hex_to_rgba(col)
        sim.ids.alpha_name.text = alpha_label(u)
        sim.ids.alpha_name.color = self.hex_to_rgba(col)
        sim.ids.alpha_sub.text  = get_alpha_sublabel(u)

    # ── Preview & harvest time ────────────────────────────────
    def _hide_preview(self):
        container = self.sim_tab.ids.preview_container
        container.clear_widgets()
        container.height = 0

    def _render_plant_preview(self, plant):
        container = self.sim_tab.ids.preview_container
        container.clear_widgets()

        # Build a stat card preview
        card = BoxLayout(orientation="vertical", size_hint_y=None,
                         height=dp(190), padding=dp(12), spacing=dp(4))
        _make_card_bg(card, (0.078, 0.106, 0.125, 1),
                      self.hex_to_rgba(TIER_COLORS.get(plant["tier"], MUTED)),
                      radius=6)

        # Header row
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24))
        tier_col = TIER_COLORS.get(plant["tier"], TEXT)
        tier_lbl = Label(text=f"[{plant['tier']}]", color=self.hex_to_rgba(tier_col),
                         font_name=FONT_MONO, font_size=sp(13), bold=True, size_hint_x=0.2)
        name_lbl = Label(text=f"  {plant['nama']}", color=self.hex_to_rgba(TEXT),
                         font_name=FONT_MONO, font_size=sp(13), bold=True, size_hint_x=0.8)
        header.add_widget(tier_lbl)
        header.add_widget(name_lbl)
        card.add_widget(header)

        cat_lbl = Label(text=plant["kategori"], color=self.hex_to_rgba(MUTED),
                        font_name=FONT_MONO, font_size=sp(9), size_hint_y=None, height=dp(14))
        card.add_widget(cat_lbl)

        # Stats grid 2x
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(110), spacing=dp(4))
        if plant["isBerkali"]:
            stats = [
                ("Durasi",      f"{plant['durasi']} jam"),
                ("Hasil",       f"{plant['minBuah']}-{plant['maxBuah']} {plant['satuan']}"),
                ("Berat Rata²", plant["beratDisplay"]),
                ("Harga Jual",  plant["hargaJualStr"]),
                ("Harga Bibit", f"{plant['hargaBibit']} LPG"),
            ]
        else:
            stats = [
                ("Durasi",       f"{plant['durasi']} jam"),
                ("Hasil Panen",  plant["hasilPanenDisplay"]),
                ("Harga Jual",   f"{plant['hargaJual']} LPG"),
                ("Harga Bibit",  f"{plant['hargaBibit']} LPG"),
            ]
        for lbl, val in stats:
            cell = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(46),
                             padding=[dp(6), dp(4)])
            _make_cell_bg(cell, (0.027, 0.035, 0.043, 1))
            cell.add_widget(Label(text=lbl, color=self.hex_to_rgba(LABEL_CLR), font_name=FONT_MONO,
                                  font_size=sp(8), bold=True, size_hint_y=None, height=dp(14)))
            cell.add_widget(Label(text=val, color=self.hex_to_rgba(TEXT), font_name=FONT_MONO,
                                  font_size=sp(11), bold=True, size_hint_y=None, height=dp(20)))
            grid.add_widget(cell)
        card.add_widget(grid)

        container.add_widget(card)
        container.height = dp(200)

    def _update_harvest_time(self):
        if not self.selected_plant:
            return
        sim = self.sim_tab
        ht = hitung_waktu_panen(sim.ids.dt_input.text, self.selected_plant["durasi"])
        self.harvest_time = ht
        if ht:
            sim.ids.harvest_lbl.text = f"Estimasi Panen: {format_datetime_id(ht)}"
            self._tick_countdown()
        else:
            sim.ids.harvest_lbl.text = "Format waktu tidak valid (YYYY-MM-DD HH:MM)"
            sim.ids.countdown_lbl.text = ""
            if self._countdown_event:
                self._countdown_event.cancel()
                self._countdown_event = None

    def _tick_countdown(self, *_):
        if not self.harvest_time:
            return
        sim = self.sim_tab
        sim.ids.countdown_lbl.text = format_countdown(self.harvest_time)
        # Schedule next tick
        if self._countdown_event:
            self._countdown_event.cancel()
        self._countdown_event = Clock.schedule_interval(self._tick_countdown_once, 1.0)

    def _tick_countdown_once(self, *_):
        if not self.harvest_time:
            return False
        sim = self.sim_tab
        sim.ids.countdown_lbl.text = format_countdown(self.harvest_time)
        return True  # repeat

    # ── Reset ─────────────────────────────────────────────────
    def reset_all(self):
        sim = self.sim_tab
        sim.ids.cat_spinner.text  = "Pilih kategori"
        sim.ids.plant_spinner.text = "Pilih kategori dulu"
        sim.ids.plant_spinner.values = []
        sim.ids.plant_spinner.disabled = True
        self._hide_preview()
        self.selected_plant = None
        self.harvest_time   = None
        sim.ids.harvest_lbl.text    = ""
        sim.ids.countdown_lbl.text  = ""
        sim.ids.alpha_slider.value = 0
        sim.ids.iter_input.text    = "10"
        sim.ids.dt_input.text      = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self._countdown_event:
            self._countdown_event.cancel()
            self._countdown_event = None
        self._clear_results()

    def _clear_results(self):
        sim = self.sim_tab
        sim.ids.results_container.clear_widgets()
        sim.ids.results_container.height = 0
        sim.ids.results_placeholder.height = dp(200)

    # ── Run simulation ────────────────────────────────────────
    def run_simulation(self):
        if self.is_simulating:
            return
        if not self.selected_plant:
            self._show_error("Peringatan", "Pilih tanaman terlebih dahulu!")
            return
        try:
            iterasi = int(self.sim_tab.ids.iter_input.text)
            if iterasi < 1 or iterasi > 100_000:
                raise ValueError
        except (ValueError, TypeError):
            self._show_error("Peringatan", "Iterasi harus 1 - 100.000!")
            return

        user_alpha = float(self.sim_tab.ids.alpha_slider.value) / 100.0
        plant      = self.selected_plant

        # Tampilkan loading
        self.is_simulating = True
        self.sim_tab.ids.run_btn.text = "Menghitung..."
        self.sim_tab.ids.run_btn.disabled = True
        self._show_loading()

        def _worker():
            try:
                if plant["isBerkali"]:
                    result = simulasi_berkali(plant, iterasi, user_alpha)
                else:
                    result = simulasi_sekali(plant, iterasi, user_alpha)
                # Kembali ke main thread via Clock
                Clock.schedule_once(lambda dt: self._show_results(result, plant, iterasi), 0)
            except Exception as e:
                err_msg = f"Simulasi gagal: {e}"
                Clock.schedule_once(lambda dt: self._on_sim_error(err_msg), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_sim_error(self, msg):
        self._hide_loading()
        self.is_simulating = False
        self.sim_tab.ids.run_btn.text = "JALANKAN SIMULASI"
        self.sim_tab.ids.run_btn.disabled = False
        self._show_error("Error", msg)

    # ── Loading popup ─────────────────────────────────────────
    def _show_loading(self):
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        lbl = Label(text="Menjalankan simulasi...\nMohon tunggu",
                    color=self.hex_to_rgba(TEXT), font_name=FONT_MONO,
                    font_size=sp(13), halign="center")
        content.add_widget(lbl)
        self._loading_popup = Popup(
            title="Loading",
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=False,
            background_color=self.hex_to_rgba(BG_MID),
        )
        self._loading_popup.open()

    def _hide_loading(self):
        if hasattr(self, "_loading_popup") and self._loading_popup:
            self._loading_popup.dismiss()
            self._loading_popup = None

    # ── Show results ──────────────────────────────────────────
    def _show_results(self, result, plant, iterasi):
        self._hide_loading()
        self.is_simulating = False
        self.sim_tab.ids.run_btn.text = "JALANKAN SIMULASI"
        self.sim_tab.ids.run_btn.disabled = False

        sim = self.sim_tab
        # hide placeholder
        sim.ids.results_placeholder.height = 0
        container = sim.ids.results_container
        container.clear_widgets()
        container.height = container.minimum_height

        u     = result["userAlpha"]
        u_str = f"+{u:.2f}" if u >= 0 else f"{u:.2f}"
        col   = alpha_label_color(u)

        # ── Header card ──────────────────────────────────────
        header_card = self._build_card(f"Hasil Simulasi: {plant['nama']}")
        meta_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24))
        meta_row.add_widget(self._make_label(f"Alpha: {u_str}", sp(12), col, True))
        meta_row.add_widget(self._make_label(alpha_label(u), sp(11), col, False))
        meta_row.add_widget(self._make_label(f"Tier: {plant['tier']}", sp(11),
                                              TIER_COLORS.get(plant["tier"], TEXT), False))
        if self.harvest_time:
            meta_row.add_widget(self._make_label(format_datetime_id(self.harvest_time),
                                                  sp(10), AMBER, False))
        header_card.add_widget(meta_row)
        container.add_widget(header_card)

        # ── Render by type ───────────────────────────────────
        if plant["isBerkali"]:
            self._render_berkali(container, result, plant, iterasi)
        else:
            self._render_sekali(container, result, plant, iterasi)

        # ── Grand total ──────────────────────────────────────
        gt = GrandTotalCard(
            total_text=f"{format_ribuan(result['totalHarga'])} LPG",
            sub_text=(f"{format_ribuan(result['totalFruits'])} buah dipanen  |  Bibit: {plant['hargaBibit']} LPG"
                      if plant["isBerkali"]
                      else f"{iterasi} kali panen  |  Bibit: {plant['hargaBibit']} LPG"),
        )
        container.add_widget(gt)

        # update container height
        container.height = container.minimum_height

        # scroll to top — defer ke frame berikutnya agar layout selesai
        # dihitung sebelum scroll_y diset (sebelumnya no-op + race condition).
        def _scroll_top(*_):
            sim.ids.sim_scroll.scroll_y = 1.0
        Clock.schedule_once(_scroll_top, 0)

    def _render_berkali(self, container, r, plant, iterasi):
        # Stats card
        stats_data = [
            ("Total Iterasi",  f"{iterasi}x",                          GREEN),
            ("Total Buah",     format_ribuan(r["totalFruits"]),         TEXT),
            ("Total Mutasi",   str(r["mutasiResult"]["totalMutasi"]),   AMBER),
            ("Rata² Berat",    format_gram(r["avgBeratGram"]),          TEXT),
            ("Berat Normal",   format_gram(plant["beratRataRataGram"]), MUTED),
            ("Total Harga",    f"{format_ribuan(r['totalHarga'])} LPG", AMBER),
            ("Rata² Harga",    f"{r['avgHarga']:.2f} LPG",              TEXT),
            ("Harga Dasar",    f"{plant['hargaJual']} LPG",             MUTED),
        ]
        scard = StatsCard(card_title="Statistik Panen Berkali-kali", grid_cols=4)
        for lbl, val, col in stats_data:
            scard.ids.stats_grid.add_widget(self._make_stat_cell(lbl, val, col))
        container.add_widget(scard)

        # Mutation cards
        mut_hasil = {k: v for k, v in r["mutasiResult"]["hasil"].items() if v > 0}
        if mut_hasil:
            mcard = StatsCard(card_title="Mutasi yang Terjadi", grid_cols=4)
            for k, v in mut_hasil.items():
                mcard.ids.stats_grid.add_widget(
                    self._make_stat_cell(k, str(v), RARITY_COLORS.get(k, TEXT))
                )
            container.add_widget(mcard)

        # Iterasi table (truncated)
        display_n = min(50, len(r["fruitCountResults"]))
        total_n   = len(r["fruitCountResults"])
        icard = self._build_card(f"Jumlah Buah per Iterasi (tampil {display_n}/{format_ribuan(total_n)})")
        icard.add_widget(self._build_table(
            ["No", "Jumlah Buah"],
            [(row["iterasi"], row["jumlah"]) for row in r["fruitCountResults"][:50]],
            col_widths=[0.3, 0.7],
        ))
        container.add_widget(icard)

        # Weight results table
        display_n  = min(100, len(r["weightResults"]))
        total_n    = len(r["weightResults"])
        trunc_note = f"(tampil {display_n}/{format_ribuan(total_n)} buah)" if total_n > 100 else ""
        wcard = self._build_card(f"Data per Buah {trunc_note}")
        rows = []
        for row in r["weightResults"][:100]:
            vs     = "▲" if row["beratGram"] > plant["beratRataRataGram"] else "▼"
            mut    = row["mutasi"] or "—"
            rows.append((
                row["no"],
                format_gram(row["beratGram"]),
                vs,
                mut,
                format_ribuan(row["harga"]),
            ))
        wcard.add_widget(self._build_table(
            ["No", "Berat", "vs", "Mutasi", "Harga (LPG)"],
            rows,
            col_widths=[0.12, 0.28, 0.08, 0.22, 0.30],
            row_colors=[
                (RARITY_COLORS.get(rw[3], TEXT) if rw[3] != "—" else
                 (GREEN if rw[2] == "▲" else MUTED))
                for rw in rows
            ],
        ))
        container.add_widget(wcard)

    def _render_sekali(self, container, r, plant, iterasi):
        total_mutasi = sum(1 for h in r["harvests"] if h["mutasi"])
        stats_data = [
            ("Total Panen",   f"{iterasi}x",                            GREEN),
            ("Normal Yield",  plant["hasilPanenDisplay"],               TEXT),
            ("Mutasi",        str(total_mutasi),                        AMBER),
            ("Total Harga",   f"{format_ribuan(r['totalHarga'])} LPG",  AMBER),
            ("Rata² Harga",   f"{r['avgHarga']:.2f} LPG",               TEXT),
            ("Harga Dasar",   f"{plant['hargaJual']} LPG",              MUTED),
        ]
        scard = StatsCard(card_title="Statistik Panen Sekali", grid_cols=3)
        for lbl, val, col in stats_data:
            scard.ids.stats_grid.add_widget(self._make_stat_cell(lbl, val, col))
        container.add_widget(scard)

        hcard = self._build_card("Data per Panen")
        rows = []
        for row in r["harvests"][:100]:
            mut = row["mutasi"] or "—"
            rows.append((
                row["no"],
                format_gram(row["aktualGram"]),
                mut,
                format_ribuan(row["harga"]),
            ))
        hcard.add_widget(self._build_table(
            ["No", "Hasil Aktual", "Mutasi", "Harga (LPG)"],
            rows,
            col_widths=[0.15, 0.35, 0.25, 0.25],
            row_colors=[RARITY_COLORS.get(rw[2], TEXT) if rw[2] != "—" else TEXT for rw in rows],
        ))
        container.add_widget(hcard)

    # ── UI helpers ────────────────────────────────────────────
    def _build_card(self, title: str) -> BoxLayout:
        """Buat kartu dengan title dan accent bar hijau."""
        card = BoxLayout(orientation="vertical", size_hint_y=None,
                         height=dp(60), padding=dp(12), spacing=dp(6))
        _make_card_bg(card, (0.063, 0.082, 0.094, 1),
                      (0.086, 0.639, 0.369, 1), radius=6)

        # Title
        title_lbl = Label(text=title, color=self.hex_to_rgba(TEXT),
                          font_name=FONT_MONO, font_size=sp(12), bold=True,
                          size_hint_y=None, height=dp(20))
        card.add_widget(title_lbl)
        # set height minimum
        card.height = dp(50)
        card.bind(minimum_height=lambda inst, val: setattr(inst, "height", max(val, dp(50))))
        return card

    def _make_label(self, text, font_size_val, color_hex, bold=False) -> Label:
        return Label(text=text, color=self.hex_to_rgba(color_hex),
                     font_name=FONT_MONO, font_size=font_size_val, bold=bold,
                     size_hint_y=None, height=dp(20))

    def _make_stat_cell(self, label, value, color_hex) -> BoxLayout:
        cell = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(54),
                         padding=[dp(6), dp(4)])
        _make_cell_bg(cell, (0.027, 0.035, 0.043, 1))
        cell.add_widget(Label(text=label, color=self.hex_to_rgba(LABEL_CLR),
                              font_name=FONT_MONO, font_size=sp(8), bold=True,
                              size_hint_y=None, height=dp(14)))
        cell.add_widget(Label(text=value, color=self.hex_to_rgba(color_hex),
                              font_name=FONT_MONO, font_size=sp(13), bold=True,
                              size_hint_y=None, height=dp(20)))
        return cell

    def _build_table(self, headers, rows, col_widths, row_colors=None) -> BoxLayout:
        """Bangun tabel sederhana (header + baris)."""
        wrapper = BoxLayout(orientation="vertical", size_hint_y=None,
                            height=dp(28) + dp(26) * min(len(rows), 100),
                            spacing=dp(1))

        # Header row
        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        for i, h in enumerate(headers):
            lbl = Label(text=h, color=self.hex_to_rgba(LABEL_CLR),
                        font_name=FONT_MONO, font_size=sp(10), bold=True,
                        size_hint_x=col_widths[i])
            _make_label_bg(lbl, (0.078, 0.106, 0.125, 1))
            header_row.add_widget(lbl)
        wrapper.add_widget(header_row)

        # Data rows
        for r_idx, row in enumerate(rows):
            row_widget = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
            for i, cell_val in enumerate(row):
                color = TEXT
                if row_colors and r_idx < len(row_colors):
                    color = row_colors[r_idx]
                lbl = Label(text=str(cell_val), color=self.hex_to_rgba(color),
                            font_name=FONT_MONO, font_size=sp(9),
                            size_hint_x=col_widths[i])
                bg_color = (0.047, 0.063, 0.078, 1) if r_idx % 2 == 0 else (0.027, 0.035, 0.043, 1)
                _make_label_bg(lbl, bg_color)
                row_widget.add_widget(lbl)
            wrapper.add_widget(row_widget)

        return wrapper

    # ── Katalog editor ────────────────────────────────────────
    def _build_katalog_editor(self):
        """Bangun editor katalog dari data terkini."""
        plants_list = self.katalog_tab.ids.plants_list
        mutasi_list = self.katalog_tab.ids.mutasi_list
        plants_list.clear_widgets()
        mutasi_list.clear_widgets()

        # Plants — berkali
        for plant in self.plants_berkali:
            card = PlantEditCard(
                title_text=f"[{plant['tier']}] {plant['nama']}",
                subtitle_text="Sekali Tanam, Panen Berkali-kali",
                accent_color=TIER_COLORS.get(plant["tier"], MUTED),
                plant_raw=plant["_raw"],
                category="berkali",
            )
            # Field editor — semua field asli dari JSON
            raw = plant["_raw"]
            card.fields = [
                ("Nama Tanaman",   "nama_tanaman",      raw.get("nama_tanaman", "")),
                ("Tier (E/D/C/B/A)", "tier",            raw.get("tier", "")),
                ("Durasi (jam)",    "durasi",            raw.get("durasi", "")),
                ("Hasil Panen",     "hasil_panen_range", raw.get("hasil_panen_range", "")),
                ("Berat Rata²",     "berat_rata_rata",   raw.get("berat_rata_rata", "")),
                ("Harga Bibit",     "harga_bibit",       raw.get("harga_bibit", 0)),
                ("Harga Jual",      "harga_jual",        raw.get("harga_jual", "")),
            ]
            plants_list.add_widget(card)

        # Plants — sekali
        for plant in self.plants_sekali:
            card = PlantEditCard(
                title_text=f"[{plant['tier']}] {plant['nama']}",
                subtitle_text="Sekali Tanam, Sekali Panen",
                accent_color=TIER_COLORS.get(plant["tier"], MUTED),
                plant_raw=plant["_raw"],
                category="sekali",
            )
            raw = plant["_raw"]
            card.fields = [
                ("Nama Tanaman",   "nama_tanaman",      raw.get("nama_tanaman", "")),
                ("Tier (E/D/C/B/A)", "tier",            raw.get("tier", "")),
                ("Durasi Panen",    "durasi_panen",      raw.get("durasi_panen", "")),
                ("Hasil Panen",     "hasil_panen",       raw.get("hasil_panen", "")),
                ("Harga Bibit (LPG)", "harga_bibit_lpg", raw.get("harga_bibit_lpg", 0)),
                ("Harga Jual (LPG)",  "harga_jual_lpg",  raw.get("harga_jual_lpg", 0)),
            ]
            plants_list.add_widget(card)

        # Mutasi
        for name in DEFAULT_MUTASI:
            card = MutasiEditCard(
                mutasi_name=name,
                accent_color=RARITY_COLORS.get(name, TEXT),
                rarity_label=f"Default chance: {DEFAULT_MUTASI[name]:.5f}  |  Multiplier: {DEFAULT_MULTIPLIER[name]}x",
                hint_text=f"Chance 0..1 (mis. 0.025). Multiplier > 0 (mis. 1.5).",
                chance_value=str(ACTIVE_MUTASI.get(name, DEFAULT_MUTASI[name])),
                mult_value=str(RARITY_MULTIPLIER.get(name, DEFAULT_MULTIPLIER[name])),
            )
            mutasi_list.add_widget(card)

    # ── Save all edits ────────────────────────────────────────
    def save_all_edits(self):
        """Kumpulkan semua nilai dari editor dan simpan ke JSON internal storage."""
        try:
            # ── Plants ────────────────────────────────────────
            new_shop = {
                "tanaman_sekali_tanam_panen_berkali_kali": [],
                "tanaman_sekali_tanam_sekali_panen":       [],
            }
            plants_list = self.katalog_tab.ids.plants_list
            # Catatan: Kivy .children mengembalikan urutan TERBALIK dari insert.
            # Pakai reversed(...) agar urutan tanaman saat disimpan sama dengan
            # urutan tampil di editor (mencegah data corruption urutan JSON).
            for card in reversed(plants_list.children):
                if not isinstance(card, PlantEditCard):
                    continue
                raw = dict(card.plant_raw)
                edits = card.collect_values()
                # Apply edits
                for field, val in edits.items():
                    if field in ("harga_bibit", "harga_bibit_lpg", "harga_jual_lpg"):
                        try:
                            raw[field] = int(val)
                        except ValueError:
                            raise ValueError(f"{card.title_text}: {field} harus integer")
                    elif field == "no":
                        try:
                            raw[field] = int(val)
                        except ValueError:
                            pass
                    else:
                        raw[field] = val
                # validate required
                if "nama_tanaman" not in raw or not raw["nama_tanaman"]:
                    raise ValueError("Nama tanaman tidak boleh kosong")
                if "tier" not in raw or raw["tier"] not in ("E", "D", "C", "B", "A"):
                    raise ValueError(f"Tier harus E/D/C/B/A (dapat: {raw.get('tier')})")

                if card.category == "berkali":
                    new_shop["tanaman_sekali_tanam_panen_berkali_kali"].append(raw)
                else:
                    new_shop["tanaman_sekali_tanam_sekali_panen"].append(raw)

            # ── Mutasi ────────────────────────────────────────
            new_chance = {}
            new_mult   = {}
            mutasi_list = self.katalog_tab.ids.mutasi_list
            # reversed(...) agar urutan key di JSON sama dengan DEFAULT_MUTASI
            for card in reversed(mutasi_list.children):
                if not isinstance(card, MutasiEditCard):
                    continue
                chance, mult = card.collect()
                new_chance[card.mutasi_name] = chance
                new_mult[card.mutasi_name]   = mult

            # Save to storage
            save_shop_data(new_shop)
            save_mutasi_data(new_chance, new_mult)

            # Reload in-memory state
            global ACTIVE_MUTASI, RARITY_MULTIPLIER
            ACTIVE_MUTASI     = dict(DEFAULT_MUTASI)
            RARITY_MULTIPLIER = dict(DEFAULT_MULTIPLIER)
            for k in DEFAULT_MUTASI:
                ACTIVE_MUTASI[k]     = new_chance.get(k, DEFAULT_MUTASI[k])
                RARITY_MULTIPLIER[k] = new_mult.get(k, DEFAULT_MULTIPLIER[k])

            # Reload plants
            self.plants_berkali = [build_plant_info(i, "berkali")
                                   for i in new_shop["tanaman_sekali_tanam_panen_berkali_kali"]]
            self.plants_sekali  = [build_plant_info(i, "sekali")
                                   for i in new_shop["tanaman_sekali_tanam_sekali_panen"]]
            # Refresh current_plants jika sudah dipilih kategori
            if self.current_category == "berkali":
                self.current_plants = self.plants_berkali
                self.sim_tab.ids.plant_spinner.values = [f"[{p['tier']}] {p['nama']}"
                                                          for p in self.current_plants]
            elif self.current_category == "sekali":
                self.current_plants = self.plants_sekali
                self.sim_tab.ids.plant_spinner.values = [f"[{p['tier']}] {p['nama']}"
                                                          for p in self.current_plants]

            # Refresh selected_plant ke dict baru (sebelumnya referensi stale
            # ke plant lama → simulasi pakai data sebelum edit).
            if self.selected_plant is not None and self.current_plants:
                old = self.selected_plant
                self.selected_plant = next(
                    (p for p in self.current_plants
                     if p["nama"] == old["nama"] and p["tier"] == old["tier"]),
                    None,
                )
                if self.selected_plant is None:
                    # tanaman hilang / di-rename → reset pilihan
                    self.sim_tab.ids.plant_spinner.text = "Pilih tanaman"
                    self._hide_preview()
                else:
                    self._render_plant_preview(self.selected_plant)
                    self._update_harvest_time()

            self._show_info("Tersimpan", "Semua perubahan berhasil disimpan ke internal storage.")
        except ValueError as e:
            self._show_error("Validasi Gagal", str(e))
        except Exception as e:
            self._show_error("Error", f"Gagal menyimpan: {e}")

    def reset_to_default(self):
        """Reset shop & mutasi ke nilai bawaan."""
        try:
            shop_default, mutasi_default = reset_all_to_default()
            # Reload global state
            global ACTIVE_MUTASI, RARITY_MULTIPLIER
            ACTIVE_MUTASI     = dict(mutasi_default["chance"])
            RARITY_MULTIPLIER = dict(mutasi_default["multiplier"])

            self._raw_shop     = shop_default
            self.plants_berkali = [build_plant_info(i, "berkali")
                                   for i in shop_default["tanaman_sekali_tanam_panen_berkali_kali"]]
            self.plants_sekali  = [build_plant_info(i, "sekali")
                                   for i in shop_default["tanaman_sekali_tanam_sekali_panen"]]

            # Rebuild katalog editor
            self._build_katalog_editor()

            # Reset spinner simulasi
            self.sim_tab.ids.cat_spinner.text  = "Pilih kategori"
            self.sim_tab.ids.plant_spinner.text = "Pilih kategori dulu"
            self.sim_tab.ids.plant_spinner.values = []
            self.sim_tab.ids.plant_spinner.disabled = True
            self._hide_preview()
            self.selected_plant = None
            self._clear_results()

            # Cleanup countdown timer (sebelumnya tidak di-cancel → stale tick)
            self.harvest_time = None
            sim = self.sim_tab
            sim.ids.harvest_lbl.text   = ""
            sim.ids.countdown_lbl.text = ""
            if self._countdown_event:
                self._countdown_event.cancel()
                self._countdown_event = None

            self._show_info("Reset Berhasil",
                            "Semua data tanaman & mutasi dikembalikan ke nilai bawaan.")
        except Exception as e:
            self._show_error("Error", f"Gagal reset: {e}")

    # ── Popup helpers ─────────────────────────────────────────
    def _show_error(self, title: str, message: str):
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        lbl = Label(text=message, color=self.hex_to_rgba(TEXT),
                    font_name=FONT_MONO, font_size=sp(12),
                    halign="center", valign="middle",
                    text_size=(Window.width * 0.7, None))
        btn = Button(text="OK", color=(0, 0, 0, 1),
                     font_name=FONT_MONO, font_size=sp(13), bold=True,
                     size_hint_y=None, height=dp(44),
                     background_color=(0, 0, 0, 0))
        _make_cell_bg(btn, (0.086, 0.639, 0.369, 1), radius=6)
        btn.bind(on_release=lambda *_: popup.dismiss())
        content.add_widget(lbl)
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.4),
                      auto_dismiss=True, background_color=self.hex_to_rgba(BG_MID))
        popup.open()

    def _show_info(self, title: str, message: str):
        self._show_error(title, message)

    # ── Lifecycle ─────────────────────────────────────────────
    def on_pause(self):
        # Android: kembalikan True agar app di-pause (bukan di-kill) saat
        # user switch app. Tanpa ini, app di-kill OS dan state hilang.
        return True

    def on_resume(self):
        # Refresh countdown display after resuming from pause
        if self.harvest_time:
            self._tick_countdown()

    def on_stop(self):
        if self._countdown_event:
            self._countdown_event.cancel()
            self._countdown_event = None


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # On desktop, set window size for testing
    if not hasattr(sys, "android_api_version"):
        try:
            Window.size = (412, 915)  # pixel 6 size
        except Exception:
            pass
    GachaFarmApp().run()

