import streamlit as st
import streamlit.components.v1 as components
import requests
import time
from datetime import datetime
from collections import Counter
import subprocess
import platform

st.set_page_config(
    page_title="VisionGuard",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "http://localhost:8000"

if "activated" not in st.session_state:
    st.session_state.activated = False


# LANDING PAGE — uses components.html so HTML renders fully
if not st.session_state.activated:

    st.markdown("""
    <style>
    #MainMenu,footer,header,.stDeployButton{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    section[data-testid="stSidebar"]{display:none!important}
    .stApp>div:first-child{padding:0!important}
    html,body,.stApp{background:#000!important;overflow:hidden!important}
    div[data-testid="stVerticalBlock"]>div{padding:0!important}
    .stButton>button{
        background:transparent!important;
        border:1px solid #00ff8c!important;
        color:#00ff8c!important;
        font-family:'Rajdhani',sans-serif!important;
        font-size:18px!important;
        font-weight:700!important;
        letter-spacing:8px!important;
        padding:18px 60px!important;
        border-radius:0!important;
        transition:all .3s!important;
        text-transform:uppercase!important;
        width:100%!important;
    }
    .stButton>button:hover{
        background:rgba(0,255,140,.1)!important;
        box-shadow:0 0 30px rgba(0,255,140,.3)!important;
        color:#00ff8c!important;
        border-color:#00ff8c!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Full landing page via components.html — renders raw HTML/CSS/JS
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000;overflow:hidden;font-family:'Share Tech Mono',monospace;width:100%;height:100vh}

/* Grid */
body::before{
    content:'';position:fixed;top:0;left:0;right:0;bottom:0;
    background-image:linear-gradient(rgba(0,255,140,.04) 1px,transparent 1px),
                     linear-gradient(90deg,rgba(0,255,140,.04) 1px,transparent 1px);
    background-size:50px 50px;
    animation:gridMove 20s linear infinite;pointer-events:none;
}
@keyframes gridMove{
    0%{transform:perspective(600px) rotateX(8deg) translateY(0)}
    100%{transform:perspective(600px) rotateX(8deg) translateY(50px)}
}

/* Ticker */
.ticker-wrap{
    position:fixed;top:0;left:0;right:0;overflow:hidden;
    white-space:nowrap;border-bottom:1px solid rgba(0,255,140,.1);
    padding:6px 0;z-index:100;background:#000;
}
.ticker{
    display:inline-block;
    animation:tickMove 25s linear infinite;
    font-size:10px;color:rgba(0,255,140,.45);letter-spacing:3px;
}
@keyframes tickMove{from{transform:translateX(100vw)}to{transform:translateX(-200%)}}

/* Side panels */
.side-left,.side-right{
    position:fixed;top:50%;transform:translateY(-50%);
    font-size:9px;letter-spacing:2px;color:rgba(0,255,140,.2);
    line-height:2.2;z-index:10;
}
.side-left{left:32px}
.side-right{right:32px;text-align:right}

/* Bottom */
.btm{
    position:fixed;bottom:0;left:0;right:0;
    padding:10px 40px;border-top:1px solid rgba(0,255,140,.08);
    display:flex;justify-content:space-between;
    font-size:9px;letter-spacing:2px;color:rgba(0,255,140,.2);
    z-index:10;background:#000;
}

/* Center wrap */
.center{
    position:fixed;top:50%;left:50%;
    transform:translate(-50%,-50%);
    display:flex;flex-direction:column;
    align-items:center;z-index:20;
    margin-top:20px;
}

/* Radar */
.radar-wrap{position:relative;width:300px;height:300px;margin-bottom:24px;flex-shrink:0}
.rc{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);border-radius:50%;border:1px solid rgba(0,255,140,.12)}
.rc1{width:300px;height:300px}
.rc2{width:225px;height:225px;border-color:rgba(0,255,140,.18)}
.rc3{width:150px;height:150px;border-color:rgba(0,255,140,.26)}
.rc4{width:75px;height:75px;border-color:rgba(0,255,140,.38)}
.rch{position:absolute;top:50%;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,255,140,.15),transparent)}
.rcv{position:absolute;left:50%;top:0;bottom:0;width:1px;background:linear-gradient(180deg,transparent,rgba(0,255,140,.15),transparent)}
.rsweep{position:absolute;top:50%;left:50%;width:150px;height:150px;transform-origin:0 0;animation:sweep 3s linear infinite}
.rsweep::before{
    content:'';position:absolute;top:0;left:0;width:150px;height:150px;
    border-radius:50% 50% 0 0/50% 50% 0 0;
    background:conic-gradient(from -5deg,transparent 0deg,rgba(0,255,140,.45) 30deg,rgba(0,255,140,.15) 60deg,transparent 90deg);
    transform-origin:bottom left;
}
.rsweep::after{
    content:'';position:absolute;top:0;left:0;width:2px;height:150px;
    background:linear-gradient(180deg,rgba(0,255,140,.9),transparent);
    transform-origin:bottom left;
}
@keyframes sweep{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.blip{position:absolute;width:6px;height:6px;border-radius:50%;background:#00ff8c;box-shadow:0 0 8px #00ff8c,0 0 16px #00ff8c;animation:blipFade 3s infinite}
.b1{top:28%;left:62%;animation-delay:.8s}
.b2{top:58%;left:74%;animation-delay:1.6s}
.b3{top:68%;left:36%;animation-delay:2.1s}
.b4{top:32%;left:28%;animation-delay:.3s}
@keyframes blipFade{0%{opacity:0;transform:scale(0)}10%{opacity:1;transform:scale(1.5)}30%{opacity:.8;transform:scale(1)}100%{opacity:0;transform:scale(.5)}}
.rcenter{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:10px;height:10px;border-radius:50%;background:#00ff8c;box-shadow:0 0 20px #00ff8c}

/* Text */
.pre-title{
    font-size:11px;letter-spacing:6px;color:rgba(0,255,140,.55);
    margin-bottom:8px;animation:fid 1s ease both;
}
.main-title{
    font-family:'Rajdhani',sans-serif;font-size:64px;font-weight:700;
    letter-spacing:12px;color:#fff;line-height:1;
    animation:fid 1s ease .2s both;
}
.main-title span{color:#00ff8c}
.sub-title{
    font-size:11px;letter-spacing:4px;color:rgba(0,255,140,.4);
    margin-top:8px;animation:fid 1s ease .4s both;
}
@keyframes fid{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}

/* Stats */
.stats-row{
    display:flex;gap:32px;margin:22px 0 28px;
    animation:fiu 1s ease .6s both;align-items:center;
}
@keyframes fiu{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.si{text-align:center}
.sv{font-family:'Rajdhani',sans-serif;font-size:26px;font-weight:700;color:#00ff8c}
.sl{font-size:9px;letter-spacing:2px;color:rgba(0,255,140,.3);margin-top:2px}
.sdiv{width:1px;height:40px;background:rgba(0,255,140,.15)}

/* Warning */
.warn{
    font-size:9px;letter-spacing:2px;color:rgba(255,180,0,.45);
    margin-top:14px;animation:fiu 1s ease 1s both;text-align:center;
}
</style>
</head>
<body>

<div class="ticker-wrap">
    <span class="ticker">
        VISIONGUARD SAFETY SYSTEM &nbsp;·&nbsp;
        YOLOV8 DETECTION ENGINE ACTIVE &nbsp;·&nbsp;
        POSE ESTIMATION ENABLED &nbsp;·&nbsp;
        BYTETRACK MULTI-OBJECT TRACKING &nbsp;·&nbsp;
        MQTT ALERT BROADCASTING &nbsp;·&nbsp;
        DOCKER MICROSERVICES ARCHITECTURE &nbsp;·&nbsp;
        EDGE DEPLOYMENT · REAL-TIME INFERENCE &nbsp;·&nbsp;
        mAP50: 0.782 · PRECISION: 0.917 · RECALL: 0.701 &nbsp;·&nbsp;
    </span>
</div>

<div class="side-left">
    SYS.STATUS: ONLINE<br>
    CV.ENGINE: READY<br>
    MQTT.BROKER: ACTIVE<br>
    STREAM.SRC: WEBCAM<br>
    MODEL.VER: v2.0<br>
    EPOCHS: 50<br>
    MAP50: 0.782<br>
    PRECISION: 0.917
</div>
<div class="side-right">
    CLASSES: 10<br>
    ALERT.CLS: 2<br>
    CONF.THR: 0.65<br>
    FPS.TARGET: 15<br>
    CONTAINERS: 3<br>
    PORT.API: 8000<br>
    PORT.DASH: 8501<br>
    PORT.MQTT: 1883
</div>

<div class="btm">
    <span>VISIONGUARD · M.TECH DATA SCIENCE PROJECT</span>
    <span>COMPUTER VISION · ARCHITECTURE DEPLOYMENT</span>
    <span>INDUSTRIAL SAFETY MONITORING SYSTEM</span>
</div>

<div class="center">
    <div class="radar-wrap">
        <div class="rc rc1"></div>
        <div class="rc rc2"></div>
        <div class="rc rc3"></div>
        <div class="rc rc4"></div>
        <div class="rch"></div>
        <div class="rcv"></div>
        <div class="rsweep"></div>
        <div class="blip b1"></div>
        <div class="blip b2"></div>
        <div class="blip b3"></div>
        <div class="blip b4"></div>
        <div class="rcenter"></div>
    </div>

    <div class="pre-title">INDUSTRIAL SAFETY MONITORING</div>
    <div class="main-title">VISION<span>GUARD</span></div>
    <div class="sub-title">REAL-TIME PPE DETECTION · EDGE DEPLOYMENT</div>


    <div class="warn">⚠ AUTHORIZED PERSONNEL ONLY · ALL ACTIVITY MONITORED AND RECORDED</div>
</div>

</body>
</html>
    """, height=750, scrolling=False)

    # Button below
    col1, col2, col3 = st.columns([1.2, 1, 1.2])
    with col2:
        if st.button("ACTIVATE MONITORING", use_container_width=True):
            st.session_state.activated = True
            st.rerun()

    st.stop()


# MAIN DASHBOARD

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Inter:wght@300;400;500&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,.stApp{background:#060a0e!important;color:#c8d8e8!important;font-family:'Inter',sans-serif!important}
#MainMenu,footer,header,.stDeployButton{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none!important}
.stApp>div:first-child{padding:0!important}
.stApp::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;
background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,180,.008) 2px,rgba(0,255,180,.008) 4px);
pointer-events:none;z-index:9998}
.vg-flash{position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:9997;border:3px solid transparent}
.vg-flash.active{border-color:#ff2222;box-shadow:inset 0 0 60px rgba(255,34,34,.15),0 0 40px rgba(255,34,34,.3);animation:fb 1.5s ease-in-out infinite}
@keyframes fb{0%,100%{border-color:#ff2222}50%{border-color:#ff6666}}
.vg-header{background:linear-gradient(90deg,#080e14 0%,#0c1620 50%,#080e14 100%);border-bottom:1px solid #00ffa322;padding:12px 28px;display:flex;align-items:center;justify-content:space-between}
.vg-logo{font-family:'Rajdhani',sans-serif;font-size:22px;font-weight:700;letter-spacing:5px;color:#00ffa3}
.vg-logo span{color:#fff}
.vg-tagline{font-family:'Share Tech Mono',monospace;font-size:9px;color:#2a5a4a;letter-spacing:3px;margin-top:2px}
.vg-clock-time{font-family:'Rajdhani',sans-serif;font-size:28px;font-weight:700;color:#5a9a8a;letter-spacing:4px;text-align:center}
.vg-clock-label{font-family:'Share Tech Mono',monospace;font-size:9px;letter-spacing:3px;color:#1a4a3a;text-align:center}
.vg-pill{display:inline-flex;align-items:center;gap:8px;border-radius:20px;padding:7px 18px;font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:1px}
.vg-pill.on{background:#0a1a14;border:1px solid #00ffa344;color:#00ffa3}
.vg-pill.off{background:#1a0a0a;border:1px solid #ff444444;color:#ff4444}
.vg-pill.alrt{background:#1a0505;border:1px solid #ff2222;color:#ff4444;animation:pp 1s infinite}
@keyframes pp{0%,100%{box-shadow:0 0 0 0 rgba(255,34,34,.4)}50%{box-shadow:0 0 0 8px rgba(255,34,34,0)}}
.vg-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.vg-dot.g{background:#00ffa3;box-shadow:0 0 8px #00ffa3;animation:dp 1.5s infinite}
.vg-dot.r{background:#ff4444;box-shadow:0 0 8px #ff4444;animation:dp .6s infinite}
.vg-dot.x{background:#334}
@keyframes dp{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.7)}}
.vg-metrics{display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #0f1e2a;background:#070b0f}
.vg-metric{padding:12px 20px;border-right:1px solid #0f1e2a;transition:background .3s}
.vg-metric:last-child{border-right:none}
.vg-metric.am{background:#120808}
.vg-ml{font-family:'Share Tech Mono',monospace;font-size:9px;letter-spacing:2px;color:#2a5a4a;text-transform:uppercase;margin-bottom:4px}
.vg-mv{font-family:'Rajdhani',sans-serif;font-size:34px;font-weight:700;line-height:1;transition:color .3s}
.cg{color:#00ffa3}.cr{color:#ff3333;animation:np 1s infinite}.ca{color:#ffaa00}.cb{color:#44aaff}
@keyframes np{0%,100%{opacity:1}50%{opacity:.5}}
.vg-ms{font-family:'Share Tech Mono',monospace;font-size:9px;color:#1a4a3a;margin-top:3px}
.vg-ph{padding:9px 18px;border-bottom:1px solid #0f1e2a;display:flex;align-items:center;justify-content:space-between;background:#070b0f}
.vg-pt{font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:600;letter-spacing:4px;color:#4a8a7a;text-transform:uppercase}
.vg-tc{font-family:'Share Tech Mono',monospace;font-size:9px;color:#1a4a3a;letter-spacing:2px}
html,body,.stApp{
    background:#060a0e!important;
    color:#c8d8e8!important;
    font-family:'Inter',sans-serif!important;
    overflow:auto!important;
}
.main{overflow:auto!important}
section.main{overflow:auto!important}
div[data-testid="stAppViewContainer"]{overflow:auto!important}
.vg-fs{padding:7px 18px;border-top:1px solid #0f1e2a;background:#070b0f;display:flex;gap:20px;font-family:'Share Tech Mono',monospace;font-size:10px;color:#2a5a4a}
.vg-fs .v{color:#4a8a7a}.vg-fs .va{color:#ff4444}
.vg-aw{overflow-y:scroll;padding:10px;max-height:calc(100vh - 400px)}
.vg-aw::-webkit-scrollbar{width:3px}
.vg-aw::-webkit-scrollbar-thumb{background:#1a3a2a}
.vg-ac{border-radius:3px;padding:9px 12px;margin-bottom:5px;animation:cs .25s ease-out;position:relative}
.vg-ac::before{content:'';position:absolute;top:0;left:0;bottom:0;width:3px}
.vg-ac.h{background:linear-gradient(135deg,#150808,#0f0808);border:1px solid #ff333322}
.vg-ac.h::before{background:#ff3333}
.vg-ac.v2{background:linear-gradient(135deg,#0f0d08,#0a0c08);border:1px solid #ff880022}
.vg-ac.v2::before{background:#ff8800}
.vg-ac.f{background:linear-gradient(135deg,#080d15,#080a12);border:1px solid #4488ff22}
.vg-ac.f::before{background:#4488ff}
@keyframes cs{from{opacity:0;transform:translateX(12px)}to{opacity:1;transform:translateX(0)}}
.vg-ach{display:flex;align-items:center;justify-content:space-between;margin-bottom:2px}
.vg-at{font-family:'Rajdhani',sans-serif;font-size:12px;font-weight:700;letter-spacing:2px;text-transform:uppercase}
.vg-at.h{color:#ff5555}.vg-at.v2{color:#ffaa33}.vg-at.f{color:#5599ff}
.vg-af{font-family:'Share Tech Mono',monospace;font-size:10px;color:#2a5a4a}
.vg-am2{font-size:11px;color:#5a7a8a;margin-bottom:2px}
.vg-atm{font-family:'Share Tech Mono',monospace;font-size:9px;color:#1a3a4a}
.vg-na{text-align:center;padding:30px 16px;font-family:'Share Tech Mono',monospace;font-size:11px;color:#00ffa344;border:1px dashed #00ffa318;border-radius:4px;margin:10px;line-height:1.8}
.vg-dw{padding:10px;border-top:1px solid #0f1e2a}
.vg-dt{width:100%;border-collapse:collapse}
.vg-dt th{font-family:'Share Tech Mono',monospace;font-size:8px;letter-spacing:2px;color:#1a4a3a;text-transform:uppercase;padding:4px 8px;text-align:left;border-bottom:1px solid #0f1e2a}
.vg-dt td{font-size:11px;color:#6a8a9a;padding:5px 8px;border-bottom:1px solid #090e14}
.vg-dt td:first-child{color:#aac8d8;font-weight:500}
.vg-dt tr:hover td{background:#0a1018}
.cr2{display:flex;align-items:center;gap:6px}
.ct{flex:1;height:2px;background:#0f1e2a;border-radius:1px}
.cf{height:100%;border-radius:1px;transition:width .3s}
.cn{font-family:'Share Tech Mono',monospace;font-size:9px;color:#3a6a5a;min-width:28px}
.vg-b{display:inline-block;padding:1px 7px;border-radius:2px;font-family:'Share Tech Mono',monospace;font-size:9px;font-weight:700;letter-spacing:1px}
.vg-b.a{background:#180808;color:#ff4444;border:1px solid #ff333322}
.vg-b.s{background:#081208;color:#00cc88;border:1px solid #00cc8822}
.vg-w{display:flex;flex-direction:column;align-items:center;justify-content:center;height:260px;gap:14px}
.vg-sp{width:36px;height:36px;border:1px solid #0f2a1a;border-top-color:#00ffa3;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.vg-wt{font-family:'Share Tech Mono',monospace;font-size:11px;letter-spacing:3px;color:#1a4a3a}
.stImage img{border-radius:2px!important;width:100%!important}
button[title="View fullscreen"]{display:none!important;visibility:hidden!important;opacity:0!important}
[data-testid="StyledFullScreenButton"]{display:none!important}
.stImage > div > button{display:none!important}
.element-container button{display:none!important}
div[data-testid="stVerticalBlock"]>div{padding:0!important}
div[data-testid="stHorizontalBlock"]{gap:0!important}
</style>
<script>
function playBeep(){
    try{
        const c=new(window.AudioContext||window.webkitAudioContext)();
        const o=c.createOscillator(),g=c.createGain();
        o.connect(g);g.connect(c.destination);
        o.frequency.setValueAtTime(880,c.currentTime);
        o.frequency.setValueAtTime(660,c.currentTime+.1);
        g.gain.setValueAtTime(.3,c.currentTime);
        g.gain.exponentialRampToValueAtTime(.001,c.currentTime+.3);
        o.start(c.currentTime);o.stop(c.currentTime+.3);
    }catch(e){}
}
let lc=0;
setInterval(()=>{
    const n=document.querySelectorAll('.vg-ac').length;
    if(n>lc){playBeep();lc=n;}
},500);
</script>
""", unsafe_allow_html=True)

def play_beep():
    try:
        if platform.system() == "Darwin":
            subprocess.Popen(["afplay", "/System/Library/Sounds/Funk.aiff"])
    except:
        pass

def fetch_status():
    try: return requests.get(f"{API_URL}/status", timeout=1.5).json()
    except: return {}

def fetch_snapshot():
    try: return requests.get(f"{API_URL}/snapshot", timeout=1.5).json().get("image")
    except: return None

def fetch_alerts():
    try: return requests.get(f"{API_URL}/alerts?limit=15", timeout=1.5).json().get("alerts", [])
    except: return []

def fetch_detections():
    try: return requests.get(f"{API_URL}/detections", timeout=1.5).json()
    except: return {}
    


status     = fetch_status()
alerts     = fetch_alerts()
if "last_alert_count" not in st.session_state:
 st.session_state.last_alert_count = 0

if len(alerts) > st.session_state.last_alert_count:
  play_beep()

st.session_state.last_alert_count = len(alerts)
detections = fetch_detections()
snapshot   = fetch_snapshot()

connected   = bool(status)
stream_live = status.get("stream_connected", False)
frames      = status.get("frames_processed", 0)
inf_ms      = status.get("last_inference_ms", 0)
dets        = detections.get("detections", [])
type_counts = Counter(a.get("type","") for a in alerts)
total_a     = len(alerts)
ppe_v       = type_counts.get("ppe_violation", 0)
fall_c      = type_counts.get("fall", 0)
alert_dets  = [d for d in dets if d.get("is_alert")]
has_alerts  = len(alert_dets) > 0
now         = datetime.now().strftime("%H:%M:%S")

st.markdown(f'<div class="{"vg-flash active" if has_alerts else "vg-flash"}"></div>', unsafe_allow_html=True)

if has_alerts:
    pc,dc,st_txt = "alrt","r","!! VIOLATION DETECTED"
elif connected and stream_live:
    pc,dc,st_txt = "on","g","SYSTEM ONLINE"
else:
    pc,dc,st_txt = "off","x","CONNECTING..."

st.markdown(f"""
<div class="vg-header">
    <div>
        <div class="vg-logo">Vision<span>Guard</span></div>
        <div class="vg-tagline">INDUSTRIAL SAFETY MONITORING · EDGE DEPLOYMENT</div>
    </div>
    <div>
        <div class="vg-clock-label">SYSTEM TIME</div>
        <div class="vg-clock-time">{now}</div>
    </div>
    <div class="vg-pill {pc}">
        <div class="vg-dot {dc}"></div>{st_txt}
    </div>
</div>
""", unsafe_allow_html=True)

tc = "cr" if total_a>0 else "cg"
pc2= "cr" if ppe_v>0  else "cg"
fc = "ca" if fall_c>0 else "cg"
ic = "ca" if inf_ms>500 else "cb"

st.markdown(f"""
<div class="vg-metrics">
    <div class="vg-metric {"am" if total_a>0 else ""}">
        <div class="vg-ml">◈ Total Alerts</div>
        <div class="vg-mv {tc}">{total_a}</div>
        <div class="vg-ms">since session start</div>
    </div>
    <div class="vg-metric {"am" if ppe_v>0 else ""}">
        <div class="vg-ml">⛑ PPE Violations</div>
        <div class="vg-mv {pc2}">{ppe_v}</div>
        <div class="vg-ms">helmet / vest alerts</div>
    </div>
    <div class="vg-metric">
        <div class="vg-ml">↯ Fall Events</div>
        <div class="vg-mv {fc}">{fall_c}</div>
        <div class="vg-ms">pose anomaly detected</div>
    </div>
    <div class="vg-metric">
        <div class="vg-ml">▣ Frames Processed</div>
        <div class="vg-mv cb">{frames:,}</div>
        <div class="vg-ms">total analyzed</div>
    </div>
    <div class="vg-metric">
        <div class="vg-ml">⚡ Inference Speed</div>
        <div class="vg-mv {ic}">{inf_ms:.0f}<span style="font-size:12px;color:#1a4a3a"> ms</span></div>
        <div class="vg-ms">per frame · cpu edge</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_feed, col_right = st.columns([2, 1], gap="small")

with col_feed:
    st.markdown("""
    <div class="vg-ph">
        <div class="vg-pt">◈ Live Camera Feed</div>
        <div class="vg-tc">YOLOv8s · YOLOv8-POSE · BYTETRACK · ONNX</div>
    </div>""", unsafe_allow_html=True)

    feed_ph = st.empty()
    if snapshot:
        feed_ph.image(snapshot, use_container_width=True)
    else:
        feed_ph.markdown("""
        <div class="vg-w">
            <div class="vg-sp"></div>
            <div class="vg-wt">AWAITING STREAM...</div>
        </div>""", unsafe_allow_html=True)

    sc  = "v" if stream_live else "va"
    alc = "va" if alert_dets else "v"
    st.markdown(f"""
    <div class="vg-fs">
        <div>STREAM <span class="{sc}">● {"LIVE" if stream_live else "OFFLINE"}</span></div>
        <div>FRAMES <span class="v">{frames:,}</span></div>
        <div>LATENCY <span class="v">{inf_ms:.0f}ms</span></div>
        <div>DETECTIONS <span class="v">{len(dets)}</span></div>
        <div>ACTIVE ALERTS <span class="{alc}">{len(alert_dets)}</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="vg-ph" style="margin-top:1px">
        <div class="vg-pt">◈ Current Detections</div>
        <div class="vg-tc">CONFIDENCE · STATUS</div>
    </div>""", unsafe_allow_html=True)

    if dets:
        rows = ""
        for d in dets:
            conf = d["confidence"]
            pct  = int(conf * 100)
            bc   = "#ff4444" if d["is_alert"] else "#00cc88"
            badge= '<span class="vg-b a">ALERT</span>' if d["is_alert"] else '<span class="vg-b s">SAFE</span>'
            rows += f"""<tr>
                <td>{d['class_name']}</td>
                <td><div class="cr2"><div class="ct"><div class="cf" style="width:{pct}%;background:{bc}"></div></div>
                <span class="cn">{conf:.2f}</span></div></td>
                <td>{badge}</td></tr>"""
        st.markdown(f"""
        <div class="vg-dw">
            <table class="vg-dt">
                <thead><tr><th>Class</th><th>Confidence</th><th>Status</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="vg-dw">
            <div style="text-align:center;padding:14px;font-family:'Share Tech Mono',monospace;font-size:10px;color:#1a4a3a;letter-spacing:2px">
                NO DETECTIONS IN CURRENT FRAME
            </div>
        </div>""", unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="vg-ph">
        <div class="vg-pt">◈ Alert Log</div>
        <div class="vg-tc">REAL-TIME · MQTT</div>
    </div>""", unsafe_allow_html=True)

    if not alerts:
        st.markdown("""
        <div class="vg-na">
            ✓ ALL SYSTEMS NOMINAL<br>
            <span style="font-size:9px;color:#0a3a2a;letter-spacing:1px">no violations detected</span>
        </div>""", unsafe_allow_html=True)
    else:
        cards = ""
        for a in alerts[:14]:
            ts   = a.get("timestamp","")[:19].replace("T"," ")
            msg  = a.get("message","")
            typ  = a.get("type","")
            conf = a.get("confidence", 0)
            if "fall" in typ:
                cc,tl = "f","↯ FALL EVENT"
            elif "hardhat" in msg.lower():
                cc,tl = "h","⛑ HELMET VIOLATION"
            else:
                cc,tl = "v2","⚠ VEST VIOLATION"
            cards += f"""
            <div class="vg-ac {cc}">
                <div class="vg-ach">
                    <span class="vg-at {cc}">{tl}</span>
                    <span class="vg-af">conf {conf:.2f}</span>
                </div>
                <div class="vg-am2">{msg}</div>
                <div class="vg-atm">{ts}</div>
            </div>"""
        st.markdown(f'<div class="vg-aw">{cards}</div>', unsafe_allow_html=True)

time.sleep(0.25)
st.rerun()