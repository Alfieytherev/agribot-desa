"""
AgriBot Desa - Agent Tools
Farming tools: weather, market prices, pest/disease ID, crop calendar
Author: Alfieytherev
"""

import json
import random
from pathlib import Path
from langchain_core.tools import tool

KB_PATH = Path(__file__).parent.parent / "knowledge"


@tool
def get_weather_info(location: str) -> str:
    """
    Get farming weather forecast for a given location in Indonesia.
    Use this when farmer asks about weather, rain, or planting conditions.
    Input: city or region name in Indonesia (e.g. 'Yogyakarta', 'Jawa Tengah')
    """
    # TODO: Replace with real BMKG API call
    # GET https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={location_code}
    mock_data = {
        "lokasi": location,
        "hari_ini": "Cerah berawan, suhu 28-32°C",
        "besok": "Hujan ringan sore hari, suhu 26-30°C",
        "kelembaban": "75%",
        "rekomendasi": "Cocok untuk penyemprotan pestisida pagi hari sebelum jam 10.",
    }
    return json.dumps(mock_data, ensure_ascii=False)


@tool
def get_market_price(commodity: str) -> str:
    """
    Get current market price for an agricultural commodity.
    Use this when farmer asks about prices of crops, vegetables, or commodities.
    Input: commodity name in Bahasa Indonesia (e.g. 'padi', 'cabai', 'jagung')
    """
    # TODO: Replace with real Harga Pangan API
    # GET https://panelharga.badanpangan.go.id/data/...
    mock_prices = {
        "padi": {"harga": "Rp 5.500/kg", "trend": "stabil", "pasar": "Induk Cipinang"},
        "cabai": {"harga": "Rp 35.000/kg", "trend": "naik", "pasar": "Kramat Jati"},
        "jagung": {"harga": "Rp 4.200/kg", "trend": "turun", "pasar": "Induk Cipinang"},
        "bawang": {"harga": "Rp 28.000/kg", "trend": "stabil", "pasar": "Kramat Jati"},
        "kedelai": {"harga": "Rp 9.000/kg", "trend": "naik", "pasar": "Induk Cipinang"},
    }
    commodity_lower = commodity.lower()
    for key, data in mock_prices.items():
        if key in commodity_lower:
            return json.dumps({
                "komoditas": commodity,
                **data,
                "update": "Hari ini"
            }, ensure_ascii=False)

    return json.dumps({
        "komoditas": commodity,
        "pesan": "Data harga belum tersedia. Cek di pasar induk terdekat atau aplikasi Info Pangan.",
    }, ensure_ascii=False)


@tool
def identify_pest_disease(description: str) -> str:
    """
    Identify crop pest or disease based on farmer's description of symptoms.
    Use this when farmer describes problems with their crops: yellowing leaves,
    holes, spots, wilting, unusual growth, etc.
    Input: description of symptoms in Bahasa Indonesia
    """
    hama_file = KB_PATH / "hama.json"
    if hama_file.exists():
        with open(hama_file, "r", encoding="utf-8") as f:
            hama_db = json.load(f)
        # Simple keyword matching (replace with vector search for production)
        desc_lower = description.lower()
        for item in hama_db:
            keywords = item.get("keywords", [])
            if any(kw in desc_lower for kw in keywords):
                return json.dumps(item, ensure_ascii=False)

    # Fallback mock response
    mock_response = {
        "gejala": description,
        "kemungkinan_penyebab": [
            {
                "nama": "Kekurangan Nitrogen",
                "probabilitas": "tinggi",
                "solusi": "Tambahkan pupuk urea 50 kg/ha, siramkan di sekitar pangkal tanaman.",
            },
            {
                "nama": "Serangan Wereng Coklat",
                "probabilitas": "sedang",
                "solusi": "Semprotkan insektisida berbahan aktif imidakloprid, dosis sesuai label.",
            },
        ],
        "saran": "Kirim foto tanaman untuk diagnosis lebih akurat.",
    }
    return json.dumps(mock_response, ensure_ascii=False)


@tool
def get_crop_calendar(crop: str, region: str = "Jawa") -> str:
    """
    Get recommended planting calendar for a specific crop and region.
    Use this when farmer asks when to plant, harvest schedule, or seasonal advice.
    Input: crop name and region (e.g. crop='padi', region='Jawa Tengah')
    """
    calendars = {
        "padi": {
            "musim_tanam_1": "Oktober - November (musim hujan)",
            "musim_tanam_2": "Maret - April (musim kemarau)",
            "umur_panen": "110-120 hari setelah tanam",
            "varietas_anjuran": ["Ciherang", "Inpari 32", "Memberamo"],
            "tips": "Olah tanah 2 minggu sebelum tanam. Gunakan bibit berumur 21 hari.",
        },
        "jagung": {
            "musim_tanam_1": "September - Oktober",
            "musim_tanam_2": "Februari - Maret",
            "umur_panen": "90-100 hari setelah tanam",
            "varietas_anjuran": ["BISI-18", "Pioneer P27", "NK 212"],
            "tips": "Jarak tanam 75x25 cm. Pemupukan dasar saat tanam, susulan umur 30 hari.",
        },
        "cabai": {
            "musim_tanam_1": "Mei - Juni (kemarau, butuh irigasi)",
            "musim_tanam_2": "Agustus - September",
            "umur_panen": "75-85 hari setelah tanam",
            "varietas_anjuran": ["Lado F1", "Kencana F1", "TM 999"],
            "tips": "Semai benih 30 hari sebelum tanam. Pasang mulsa plastik untuk menekan gulma.",
        },
    }

    crop_lower = crop.lower()
    for key, data in calendars.items():
        if key in crop_lower:
            return json.dumps({
                "tanaman": crop,
                "wilayah": region,
                **data
            }, ensure_ascii=False)

    return json.dumps({
        "tanaman": crop,
        "pesan": f"Kalender tanam untuk {crop} belum tersedia. "
                 "Hubungi penyuluh pertanian (PPL) setempat untuk rekomendasi.",
    }, ensure_ascii=False)
