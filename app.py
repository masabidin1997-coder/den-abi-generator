<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Den Abi Traffic | Strict Mode</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0f172a; color: white; overflow: hidden; }
        iframe { width: 100%; height: calc(100vh - 80px); border: none; background: white; }
        .glass { background: rgba(15, 23, 42, 0.98); backdrop-filter: blur(20px); }
        .btn-strict { background: linear-gradient(135deg, #1e40af 0%, #7e22ce 100%); transition: all 0.3s ease; }
    </style>
</head>
<body>

    <div class="h-20 border-b border-white/10 flex items-center justify-between px-8 shadow-2xl bg-slate-900 z-50 relative">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 btn-strict rounded-xl flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">DA</div>
            <div>
                <p class="text-[10px] text-blue-400 font-black tracking-widest uppercase mb-1">Strict Antrean</p>
                <p id="target-user" class="text-sm font-bold text-slate-100 italic">prostream.my.id</p>
            </div>
        </div>

        <div class="flex flex-col items-center">
            <div class="flex items-center gap-3">
                <span id="timer" class="text-4xl font-black tabular-nums">60</span>
                <span class="text-[10px] text-slate-500 font-bold mt-2 uppercase tracking-widest">Detik</span>
            </div>
            <div class="w-48 bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1">
                <div id="bar" class="bg-blue-500 h-full w-full transition-all duration-1000"></div>
            </div>
        </div>

        <div class="hidden md:block">
            <div class="bg-blue-500/10 px-6 py-2 rounded-2xl border border-blue-500/20">
                <p id="status-badge" class="text-blue-400 font-black text-xs uppercase tracking-widest animate-pulse">Monitoring...</p>
            </div>
        </div>
    </div>

    <iframe id="main-frame" src="about:blank"></iframe>

    <div id="pop-30" class="hidden fixed inset-0 glass flex items-center justify-center z-[100] p-6">
        <div class="bg-white p-10 rounded-[40px] text-center max-w-sm shadow-2xl border-t-8 border-blue-600">
            <div class="w-20 h-20 bg-blue-50 text-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-inner">
                <i class="fa-solid fa-shield-halved text-4xl"></i>
            </div>
            <h2 class="text-2xl font-black text-slate-900 mb-2">Verifikasi Lanjutan</h2>
            <p class="text-slate-500 text-sm mb-8 leading-relaxed font-medium">Timer dihentikan. Klik tombol di bawah untuk memuat iklan & melanjutkan antrean poin.</p>
            
            <button onclick="forceAdInFrame()" class="w-full btn-strict text-white font-black py-5 rounded-2xl shadow-xl hover:scale-105 active:scale-95 transition-transform">
                MUAT IKLAN SEKARANG <i class="fa-solid fa-bolt ml-2 text-xs text-yellow-300"></i>
            </button>
        </div>
    </div>

    <div id="pop-finish" class="hidden fixed inset-0 glass flex items-center justify-center z-[100] p-6">
        <div class="bg-white p-10 rounded-[40px] text-center max-w-sm shadow-2xl border-t-8 border-green-500">
            <div class="text-6xl mb-6">🏆</div>
            <h2 class="text-3xl font-black text-slate-900 mb-2 tracking-tighter">MISSION COMPLETE</h2>
            <p class="text-slate-500 text-sm mb-8 font-medium italic">Poin telah divalidasi. Klik untuk reset antrean.</p>
            <button onclick="location.reload()" class="w-full bg-green-600 hover:bg-green-700 text-white font-black py-5 rounded-2xl shadow-xl transition active:scale-95">
                KLAIM & RESET <i class="fa-solid fa-rotate-right ml-2 text-xs"></i>
            </button>
        </div>
    </div>

    <script>
        const config = {
            web: "https://www.prostream.my.id/",
            ad: "https://www.effectivegatecpm.com/r8e596iax7?key=7ebb4a0d76f18954637fb30c5d8a794a"
        };

        let timeLeft = 60;
        let isRunning = true;
        const frame = document.getElementById('main-frame');
        const timerText = document.getElementById('timer');
        const bar = document.getElementById('bar');
        const badge = document.getElementById('status-badge');

        window.onload = () => {
            frame.src = config.web;
        };

        const clock = setInterval(() => {
            if(isRunning) {
                timeLeft--;
                timerText.innerText = timeLeft;
                bar.style.width = (timeLeft/60 * 100) + "%";

                if(timeLeft === 30) {
                    isRunning = false; // Hentikan paksa
                    document.getElementById('pop-30').classList.remove('hidden');
                    badge.innerText = "WAITING ACTION...";
                    badge.classList.replace('text-blue-400', 'text-yellow-400');
                }

                if(timeLeft <= 0) {
                    clearInterval(clock);
                    isRunning = false;
                    document.getElementById('pop-finish').classList.remove('hidden');
                    badge.innerText = "COMPLETED";
                    badge.classList.replace('text-blue-400', 'text-green-400');
                }
            }
        }, 1000);

        function forceAdInFrame() {
            // PERKETAT: Tidak buka tab baru. Langsung ganti src iframe.
            frame.src = config.ad;
            
            // Tutup popup & paksa timer jalan kembali
            document.getElementById('pop-30').classList.add('hidden');
            isRunning = true;
            badge.innerText = "AD RUNNING...";
            badge.classList.replace('text-yellow-400', 'text-blue-400');
        }

        // Anti-Cheat: Timer stuck/mati jika pindah tab
        document.addEventListener("visibilitychange", () => {
            if(document.hidden) {
                isRunning = false;
                badge.innerText = "PAUSED (INACTIVE)";
            } else {
                if(timeLeft !== 30 && timeLeft > 0) {
                    isRunning = true;
                    badge.innerText = "MONITORING...";
                }
            }
        });
    </script>
</body>
</html>
