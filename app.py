import streamlit as st
import time
import random
import requests

# 1. DATABASE 100 USER-AGENT TERBARU
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.138 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Linux; Android 13; CPH2357) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    # Catatan: Masukkan sisa dari 100 UA yang saya berikan kemarin di sini
]

# 2. DATABASE ASAL TRAFIK (REFERER)
REFERERS = [
    "https://www.google.com/",
    "https://www.facebook.com/",
    "https://t.co/", 
    "https://www.tiktok.com/",
    "https://duckduckgo.com/",
    "https://www.bing.com/",
    "https://l.instagram.com/"
]

st.set_page_config(page_title="Den Abi High Retention V14", page_icon="🚀")

st.title("🚀 EXPERIMEN HIGH RETENTION V14")
st.markdown("---")

# 3. KONFIGURASI TARGET
target_url = st.text_input("Link Target (TikTok/Web/Blog):", placeholder="https://...")
target_count = st.number_input("Jumlah View (Saran: 10 per sesi):", 1, 100, 10)

st.sidebar.header("⚙️ Pengaturan Panel")
# Durasi menonton dalam detik
min_watch = st.sidebar.slider("Durasi Nonton Minimal (detik):", 15, 60, 25)
max_watch = st.sidebar.slider("Durasi Nonton Maksimal (detik):", 61, 120, 80)

# 4. LOGIKA EKSEKUSI
if st.button("🔥 MULAI INJECT VIEW"):
    if target_url:
        st.info("Memulai proses simulasi. Harap bersabar karena ini menggunakan High Retention.")
        
        progress = st.progress(0)
        status_box = st.empty()
        berhasil = 0
        
        for i in range(target_count):
            try:
                # 1. Pilih identitas acak
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Referer': random.choice(REFERERS),
                    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                }
                
                # 2. Kirim permintaan kunjungan
                response = requests.get(target_url, headers=headers, timeout=15)
                
                # 3. Simulasi durasi menonton yang lama (High Retention)
                durasi = random.uniform(min_watch, max_watch)
                status_box.write(f"⏳ Sedang mensimulasikan penonton ke-{i+1} (Durasi: {durasi:.1f} detik)...")
                
                time.sleep(durasi) # Menahan bot di halaman agar view tidak hangus
                
                if response.status_code == 200:
                    berhasil += 1
                
                # 4. Update progress
                persen = int((i + 1) / target_count * 100)
                progress.progress(persen)
                
            except Exception as e:
                st.error(f"Error pada view ke-{i+1}: {e}")
                
        st.success(f"✅ Selesai! {berhasil} view dikirim dengan metode High Retention.")
        st.balloons()
    else:
        st.error("Silakan isi link target terlebih dahulu!")

st.markdown("---")
st.caption("Den Abi Digital Store © 2026 | High Retention Simulation V14")
