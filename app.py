import streamlit as st
import time
import random

# 1. STYLE UI PREMIUM (MERAH & HITAM)
st.set_page_config(page_title="View Booster V6.1", page_icon="📈")
st.markdown("""
    <style>
    .stApp { background-color: #000; color: #FFF; }
    .timer-box { 
        background: #111; border: 3px solid #FF0000; 
        padding: 30px; border-radius: 20px; text-align: center;
        margin-top: 20px;
    }
    .timer-num { font-size: 80px; font-weight: bold; color: #FF0000; }
    .points-text { color: #00FFCC; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE SEDERHANA
if 'points' not in st.session_state: st.session_state.points = 120
if 'campaigns' not in st.session_state: 
    st.session_state.campaigns = [{"url": "https://fazagafi21.blogspot.com/", "reward": 70, "time": 60}]

st.title("🔴 VIEW BOOSTER PRO")
st.markdown(f'<p class="points-text">SALDO POIN: 🪙 {st.session_state.points}</p>', unsafe_allow_html=True)

# 3. AREA TUGAS
tab1, tab2 = st.tabs(["📺 Ambil Poin", "➕ Buat Campaign"])

with tab1:
    if st.session_state.campaigns:
        task = random.choice(st.session_state.campaigns)
        
        st.markdown(f"""
            <div style="background:#111; padding:20px; border-radius:10px; border:1px solid #333;">
                <h3>Misi: Tonton Blog</h3>
                <p>Hadiah: <b>{task['reward']} Poin</b> | Durasi: <b>{task['time']} Detik</b></p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")

        # TOMBOL PENENTU: KLIK DISINI
        if st.button(f"🚀 MULAI MENONTON ({task['time']}s)"):
            # A. Buka Link Web di Tab Baru Secara Otomatis
            st.write(f'<script>window.open("{task["url"]}", "_blank");</script>', unsafe_allow_html=True)
            
            # B. Jalankan Angka Mundur Langsung di Halaman Ini
            t_placeholder = st.empty()
            for t in range(task['time'], -1, -1):
                t_placeholder.markdown(f"""
                    <div class="timer-box">
                        <p>SISA WAKTU MENONTON</p>
                        <div class="timer-num">{t}</div>
                        <p>Detik Lagi</p>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
            
            # C. Selesai & Klaim Poin
            st.session_state.points += task['reward']
            st.success(f"✅ BERHASIL! +{task['reward']} Poin ditambahkan ke saldo kamu.")
            st.balloons()
            time.sleep(3)
            st.rerun()
    else:
        st.info("Belum ada tugas. Silakan buat campaign sendiri!")

with tab2:
    st.write("Daftarkan link blog Adsterra kamu di sini.")
    # (Form pendaftaran sama seperti sebelumnya)
