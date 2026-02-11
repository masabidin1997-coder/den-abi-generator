import streamlit as st
import time
import random

# 1. SETUP UI DENGAN KONTRAS TINGGI
st.set_page_config(page_title="Siskun Pro - Den Abi", page_icon="💰", layout="centered")

st.markdown("""
    <style>
    /* Latar belakang hitam pekat agar font putih terlihat tajam */
    .stApp { 
        background-color: #000000; 
    }
    
    /* Warna teks utama dibuat putih bersih (#FFFFFF) */
    .main-text {
        color: #FFFFFF !important;
        font-size: 18px;
        font-weight: 500;
        line-height: 1.6;
    }
    
    /* Judul dengan warna gradasi neon agar mencolok */
    .title-text {
        color: #00FFCC; 
        text-shadow: 2px 2px 4px #000000;
        font-weight: 800;
    }

    /* Box tugas dengan border kontras */
    .status-box { 
        background: #111111; 
        border: 2px solid #00FFCC; 
        padding: 25px; 
        border-radius: 15px; 
        text-align: center;
        color: #FFFFFF;
    }
    
    /* Tombol dengan warna cerah */
    .stButton>button {
        background: linear-gradient(90deg, #00FFCC, #3366FF);
        color: #000000 !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
    }

    /* Warna Timer (Merah Terang) */
    .timer-text {
        color: #FF3366;
        font-size: 28px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEM DATABASE SEDERHANA
if 'db_links' not in st.session_state:
    st.session_state.db_links = ["https://fazagafi21.blogspot.com/", "https://prostream.my.id/"]

st.markdown('<h1 class="title-text">💰 ADSTERRA TRAFFIC EXCHANGE</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-text">Platform Gotong Royong Terbesar untuk Player Adsterra Indonesia.</p>', unsafe_allow_html=True)

# 3. TAMPILAN TUGAS
st.markdown('<div class="status-box">', unsafe_allow_html=True)
target = random.choice(st.session_state.db_links)
st.markdown(f'<p class="main-text">🎯 Target Kunjungan Saat Ini:</p>', unsafe_allow_html=True)
st.code(target)

if st.button("🚀 MULAI TUGAS & KLIK IKLAN"):
    # Buka link di tab baru
    st.write(f'<script>window.open("{target}", "_blank");</script>', unsafe_allow_html=True)
    
    t_box = st.empty()
    mission_box = st.empty()
    
    for t in range(60, 0, -1):
        t_box.markdown(f'<p class="timer-text">⏳ Sisa Waktu: {t} Detik</p>', unsafe_allow_html=True)
        
        # INSTRUKSI MISI KLIK (Warna Kuning agar Jelas)
        if 40 <= t <= 55:
            mission_box.warning("⚠️ MISI 1: Cari iklan Adsterra, KLIK 1x dan biarkan terbuka!")
        elif 20 <= t <= 35:
            mission_box.warning("⚠️ MISI 2: Scroll ke tengah/bawah, cari iklan lain dan KLIK 1x!")
        elif 5 <= t <= 15:
            mission_box.warning("⚠️ MISI 3: Terakhir, klik tombol atau gambar iklan mana saja!")
        else:
            mission_box.empty()
        
        time.sleep(1)
    
    st.success("✅ TUGAS SELESAI! Anda membantu komunitas hari ini.")
st.markdown('</div>', unsafe_allow_html=True)

# 4. REGISTRASI USER BARU
st.write("---")
st.markdown('<h3 class="title-text">➕ Tambahkan Blog Kamu ke Antrean</h3>', unsafe_allow_html=True)
with st.container():
    new_url = st.text_input("Masukkan URL Blog (Pastikan sudah ada Iklan Adsterra):", placeholder="https://blogkamu.blogspot.com/...")
    if st.button("DAFTARKAN SEKARANG"):
        if new_url and new_url.startswith("http"):
            st.session_state.db_links.append(new_url)
            st.balloons()
            st.success("🔥 Link kamu sudah masuk antrean acak untuk 1000+ user!")
        else:
            st.error("Format link salah! Sertakan https://")
