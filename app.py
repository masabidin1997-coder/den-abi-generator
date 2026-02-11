import streamlit as st
import time
import random

# 1. STYLE APLIKASI KONTRAS TINGGI
st.set_page_config(page_title="View Booster V6", page_icon="📈")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .header-box { background: #FF0000; padding: 20px; color: white; text-align: center; border-radius: 0 0 20px 20px; font-weight: bold; }
    .card { background: #111111; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; text-align: center; }
    .timer-display { font-size: 45px; font-weight: bold; color: #FF3366; text-shadow: 0 0 10px #FF0000; }
    .points-display { font-size: 24px; font-weight: bold; color: #00FFCC; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATABASE SESSION
if 'points' not in st.session_state: st.session_state.points = 120
if 'is_watching' not in st.session_state: st.session_state.is_watching = False
if 'campaigns' not in st.session_state: 
    st.session_state.campaigns = [{"url": "https://prostream.my.id/", "reward": 70, "time": 60}]

# --- HEADER ---
st.markdown('<div class="header-box"><h1>VIEW BOOSTER V6</h1><p>EARN POINTS BY WATCHING</p></div>', unsafe_allow_html=True)

# --- LOGIKA TOMBOL KEMBALI OTOMATIS ---
if st.session_state.is_watching:
    task = st.session_state.current_task
    st.markdown(f'<div class="card"><h3>🔴 SEDANG MENONTON...</h3><p>Jangan tutup tab blog yang baru terbuka!</p></div>', unsafe_allow_html=True)
    
    # 3. FITUR ANGKA MUNDUR
    t_container = st.empty()
    for t in range(task['time'], -1, -1):
        t_container.markdown(f'<div class="card"><p>Angka Mundur:</p><div class="timer-display">{t}</div><p>Detik Lagi</p></div>', unsafe_allow_html=True)
        time.sleep(1)
    
    # 4. AUTO-RETURN & REWARD
    st.session_state.points += task['reward']
    st.session_state.is_watching = False
    st.success(f"🔥 Selesai! +{task['reward']} Poin berhasil diklaim.")
    st.balloons()
    time.sleep(2)
    st.rerun()

# --- TAMPILAN DASHBOARD POIN ---
tab1, tab2 = st.tabs(["📺 Get Points", "➕ My Campaigns"])

with tab1:
    st.markdown(f'<div class="card"><p>Your Balance</p><p class="points-display">🪙 {st.session_state.points} Points</p></div>', unsafe_allow_html=True)
    
    if st.session_state.campaigns:
        task = random.choice(st.session_state.campaigns)
        st.markdown(f'<div class="card"><h3>{task["reward"]} Points</h3><p>Durasi: {task["time"]} Detik</p></div>', unsafe_allow_html=True)
        
        # LINK UNTUK MEMBUKA TAB BARU
        link_html = f'''
            <a href="{task["url"]}" target="_blank" onclick="window.location.reload();" style="text-decoration:none;">
                <div style="background:#FF0000; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold; font-size:20px;">
                    START WATCHING
                </div>
            </a>
        '''
        st.markdown(link_html, unsafe_allow_html=True)
        
        if st.button("KONFIRMASI MULAI"):
            st.session_state.current_task = task
            st.session_state.is_watching = True
            st.rerun()
    else:
        st.info("Belum ada tugas tersedia.")

with tab2:
    st.write("### Create New Campaign")
    # Form input tetap sama seperti V5
