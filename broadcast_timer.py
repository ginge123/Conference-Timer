import sys
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QListWidget, QListWidgetItem, QTabWidget, 
                             QSpinBox, QTimeEdit, QComboBox, QCheckBox, 
                             QColorDialog, QFileDialog, QGroupBox, QSplitter,
                             QScrollArea, QSizePolicy, QFrame, QFontComboBox,
                             QGridLayout, QMessageBox, QSlider, QStackedWidget,
                             QFormLayout, QToolButton, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate, QSize, pyqtSignal, QEvent, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon, QPainter, QAction, QBrush
import threading
import socket
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# -----------------------------------------------------------------------------
# CONSTANTS & STYLES
# -----------------------------------------------------------------------------
APP_NAME = "David's Timer"
SUBTITLE = "refusing to pay for stagetimer since 2018"
VERSION = "17.14.0"
RUN_SHEET_FILE = "run_sheet.json"
SETTINGS_FILE = "timer_settings.json"



OPERATOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Operator View</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; user-select: none; }
        * { box-sizing: border-box; outline: none; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #161b22; padding: 10px 20px; border-bottom: 1px solid #30363d; }
        .header button { background: #21262d; border: 1px solid #363b42; color: #c9d1d9; border-radius: 6px; padding: 8px 16px; font-size: 14px; font-weight: bold; cursor: pointer; }
        .header button:active { background: #161b22; }
        .header #btn_blackout.active { background: #cf222e; color: #fff; }
        .header .clock { font-size: 20px; font-weight: bold; font-family: monospace; }
        
        .main { display: flex; flex: 1; padding: 15px; gap: 15px; overflow: hidden; }
        
        /* Sidebar (Appearance) */
        .sidebar { width: 200px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
        .sidebar h3 { margin: 0 0 5px 0; color: #8b949e; font-size: 13px; text-transform: uppercase; }
        .mode-btn { background: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; padding: 12px; text-align: left; font-weight: bold; font-size: 14px; cursor: pointer; min-height: 40px; }
        .mode-btn.active { background: #1f6feb; border-color: #58a6ff; color: #fff; }
        
        /* Content Area */
        .content { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        
        /* Run List Row */
        .run-list { display: flex; gap: 15px; }
        .run-box { flex: 1; background: #1c2128; border: 2px solid #30363d; border-radius: 8px; padding: 10px; text-align: center; }
        .run-box.current { border-color: #1f6feb; background: #1f6feb; color: #fff; }
        .run-box .title { font-size: 12px; font-weight: bold; margin-bottom: 2px; opacity: 0.8; }
        .run-box .name { font-size: 16px; font-weight: bold; }
        
        /* Big Display */
        .display { background: #161b22; border: 2px solid #30363d; border-radius: 8px; padding: 15px 20px; text-align: center; flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; }
        .timer-val { font-size: 100px; font-weight: 800; font-family: monospace; color: #fff; margin: 10px 0; line-height: 1; }
        .display-bottom { width: 100%; display: flex; justify-content: center; color: #8b949e; font-size: 16px; font-weight: bold; position: absolute; top: 15px; left: 0; }
        
        /* Controls */
        .controls { display: flex; gap: 10px; height: 50px; }
        .controls button { flex: 1; border: none; border-radius: 6px; font-size: 18px; font-weight: bold; cursor: pointer; color: #fff; }
        .btn-set { background: #1c2128; border: 2px solid #30363d; }
        .btn-set.active { background: #30363d; border-color: #58a6ff; border-width: 2px;}
        .btn-play { background: #238636; }
        .btn-play.playing { background: #f85149; }
        .btn-next { background: #21262d; border: 1px solid #30363d; }
        
        /* Numpad Area */
        .numpad-container { display: flex; gap: 15px; flex: 1; min-height: 200px; }
        .numpad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; flex: 2; }
        .numpad button { background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #fff; font-size: 20px; font-weight: bold; cursor: pointer; padding: 10px; }
        .numpad button:active { background: #30363d; }
        .btn-red { background: #da3633 !important; }
        .btn-green { background: #238636 !important; }
        
        /* Quick Actions */
        .quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; flex: 1; align-content: end; margin-bottom: 5px; }
        .quick-actions button { background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #fff; font-size: 14px; font-weight: bold; cursor: pointer; padding: 10px; }
        .quick-actions button:active { background: #30363d; }
        
        /* Progress */
        .progress-container { width: 100%; height: 8px; background: #333; border-radius: 4px; overflow: hidden; margin-top: 15px; }
        .progress-bar { height: 100%; background: #238636; width: 0%; transition: width 0.5s; }
        
        .numpad-input {
            width: 100%;
            background: #1c2128;
            border: 2px solid #30363d;
            border-radius: 6px;
            padding: 10px;
            font-size: 20px;
            font-family: monospace;
            color: #58a6ff;
            text-align: right;
            margin-bottom: 6px;
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .main { flex-direction: column; overflow: auto; }
            .sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; }
            .mode-btn { flex: 1; min-width: 100px; padding: 8px; text-align: center; }
            .timer-val { font-size: 70px; }
            .content { overflow: visible; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-weight: bold; font-size: 18px; color:#58a6ff;">Operator Panel</div>
        <div style="display:flex; gap: 10px;">
            <button id="btn_blackout" onclick="cmd('blackout')">Blackout</button>
            <button onclick="cmd('flash')">Flash</button>
        </div>
        <div class="clock" id="rclock">--:--:--</div>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <h3>Appearance</h3>
            <button class="mode-btn" onclick="setMode('Countdown')">Countdown</button>
            <button class="mode-btn" onclick="setMode('Count Up')">Count Up</button>
            <button class="mode-btn" onclick="setMode('Time of Day')">Time of Day</button>
            <button class="mode-btn" onclick="setMode('Finish At')">Finish At</button>
            
            <h3 style="margin-top:20px;">Quick Guide</h3>
            <div style="font-size: 13px; color: #8b949e; line-height: 1.6;">
                • Tap numpad digits to input time (e.g. 1 3 0 = 1:30)<br>
                • Use <strong>Apply</strong> to explicitly set duration/time<br>
                • Use <strong>+ Add</strong> / <strong>- Sub</strong> to nudge<br>
                • <strong>Play</strong> toggles start/pause<br>
                • <strong>Next</strong> loads the next event
            </div>
        </div>
        
        <div class="content">
            <div class="run-list">
                <div class="run-box"><div class="title">PREVIOUS</div><div class="name" id="prev_name">Empty</div></div>
                <div class="run-box current"><div class="title">CURRENT</div><div class="name" id="curr_name">Empty</div></div>
                <div class="run-box"><div class="title">NEXT</div><div class="name" id="next_name">Empty</div></div>
            </div>
            
            <div class="display">
                <div class="display-bottom">
                    <span id="curr_mode" style="text-transform:uppercase;">OFFLINE</span>
                </div>
                <div class="timer-val" id="big_time">00:00</div>
                
                <div class="controls">
                    <button class="btn-play" id="btn_play" onclick="cmd('play_pause')">Play</button>
                    <button class="btn-next" onclick="cmd('next')">Next</button>
                </div>
                
                <div class="progress-container" style="margin-top:20px;">
                    <div class="progress-bar" id="pbar"></div>
                </div>
            </div>
            
            <div class="numpad-container">
                <div style="flex: 2;">
                    <div class="numpad-input" id="n_input">_ _ : _ _ : _ _</div>
                    <div class="numpad">
                        <button onclick="num(1)">1</button><button onclick="num(2)">2</button><button onclick="num(3)">3</button>
                        <button onclick="num(4)">4</button><button onclick="num(5)">5</button><button onclick="num(6)">6</button>
                        <button onclick="num(7)">7</button><button onclick="num(8)">8</button><button onclick="num(9)">9</button>
                        <button class="btn-red" onclick="num(-1)">C</button><button onclick="num(0)">0</button><button class="btn-green" onclick="submitPad('apply')">Apply</button>
                    </div>
                </div>
                
                <div class="quick-actions" style="margin-top: 55px;">
                    <button onclick="cmd('nudge', {value: -60})">- 1m</button>
                    <button onclick="cmd('nudge', {value: 60})">+ 1m</button>
                    <button onclick="cmd('nudge', {value: -30})">- 30s</button>
                    <button onclick="cmd('nudge', {value: 30})">+ 30s</button>
                    <button onclick="submitPad('add')">+ Add Input</button>
                    <button onclick="submitPad('sub')">- Sub Input</button>
                    <button style="grid-column: span 2;" class="btn-red" onclick="cmd('reset')">Reset Timer</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let padVal = "";
        
        function updatePadInput() {
            if(!padVal) { document.getElementById('n_input').innerText = "_ _ : _ _ : _ _"; return; }
            let s = padVal.padStart(6, '0');
            document.getElementById('n_input').innerText = s.substring(0,2) + " : " + s.substring(2,4) + " : " + s.substring(4,6);
        }
        
        function num(n) {
            if (n === -1) padVal = "";
            else if (padVal.length < 6) padVal += n;
            updatePadInput();
        }
        
        function getPadSeconds() {
            if(!padVal) return 0;
            let s = padVal.padStart(6, '0');
            return parseInt(s.substring(0,2)) * 3600 + parseInt(s.substring(2,4)) * 60 + parseInt(s.substring(4,6));
        }

        function getPadHHMM() {
           if(!padVal) return "12:00";
           let s = padVal.padStart(4, '0');
           if (s.length > 4) s = s.substring(s.length - 4);
           let h = s.substring(0,2);
           let m = s.substring(2,4);
           let hh = parseInt(h);
           let mm = parseInt(m);
           if (hh > 23) hh = 23;
           if (mm > 59) mm = 59;
           return (hh < 10 ? "0"+hh : hh) + ":" + (mm < 10 ? "0"+mm : mm);
        }
        
        function submitPad(action) {
            let s = getPadSeconds();
            if (action === "apply") {
                if(padVal !== "") cmd('set_time', { seconds: s, hhmm: getPadHHMM() });
            } else if (action === "add" && s > 0) cmd('nudge', { value: s });
            else if (action === "sub" && s > 0) cmd('nudge', { value: -s });
            padVal = "";
            updatePadInput();
        }

        function cmd(action, payload={}) {
            fetch('/api/operator/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, ...payload })
            });
        }
        
        function setMode(mode) { cmd('set_mode', { mode }); }
        
        function poll() {
            fetch('/api/operator/state').then(r => r.json()).then(d => {
                document.getElementById('rclock').innerText = d.realtime;
                document.getElementById('btn_blackout').className = d.blackout ? "active" : "";
                
                document.getElementById('prev_name').innerText = d.prev || "Empty";
                document.getElementById('curr_name').innerText = (d.curr && d.curr.title) || "Empty";
                document.getElementById('next_name').innerText = d.next || "Empty";
                
                document.getElementById('big_time').innerText = d.text;
                document.getElementById('big_time').style.color = d.color;
                
                document.getElementById('pbar').style.width = d.progress + "%";
                document.getElementById('pbar').style.backgroundColor = (d.progress >= 100 && d.is_overtime) ? '#da3633' : '#238636';
                
                let playBtn = document.getElementById('btn_play');
                if (d.running) { playBtn.innerText = "Pause"; playBtn.className = "btn-play playing"; }
                else { playBtn.innerText = "Play"; playBtn.className = "btn-play"; }
                
                if (d.curr) {
                    document.getElementById('curr_mode').innerText = d.curr.mode;
                    document.querySelectorAll('.mode-btn').forEach(b => {
                        b.className = "mode-btn";
                        if(b.innerText === d.curr.mode) b.classList.add('active');
                    });
                }
            }).catch(e => console.log(e)).finally(() => setTimeout(poll, 1000));
        }
        poll();
    </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# DATA STRUCTURES
# -----------------------------------------------------------------------------
class TimerMode:
    COUNTDOWN = "Countdown"
    COUNTUP = "Count Up"
    FINISH_AT = "Finish At"
    TOD = "Time of Day"

DEFAULT_SETTINGS = {
    "bg_color": "#141414",
    "banner_bg_color": "#141414",
    "text_color": "#ffffff",
    "header_color": "#58a6ff",
    "progress_color": "#238636",
    "message_color": "#f6e05e",
    "font_family": "Arial",
    "font_weight": "Bold",
    "timer_alignment": "Center",
    "show_logo": True,
    "show_clock": True,
    "show_progress": True,
    "smart_colors": False, 
    "bg_image_path": "",
    "bg_mode": "Cover",
    "logo_path": "",
    "scale_logo": 100,
    "scale_timer": 100,
    "scale_header": 100,
    "allow_overtime": False,
    "auto_advance": False
}

# -----------------------------------------------------------------------------
# HELPER WIDGETS
# -----------------------------------------------------------------------------
class AspectRatioWidget(QWidget):
    def __init__(self, widget, ratio=16/9, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewWrapper")
        self.widget = widget
        self.widget.setParent(self)
        self.ratio = ratio
        self.setStyleSheet("#PreviewWrapper { background-color: #000000; border: 2px solid #444; }") 

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        target_h = w / self.ratio
        if target_h > h:
            new_h = h
            new_w = h * self.ratio
        else:
            new_w = w
            new_h = target_h
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        self.widget.setGeometry(int(x), int(y), int(new_w), int(new_h))

class ColorSwatch(QPushButton):
    def __init__(self, color, callback):
        super().__init__()
        self.setObjectName("ColorSwatch")
        self.setFixedSize(40, 40)
        self.color = color
        self.callback = callback
        self.update_color(color)
        self.clicked.connect(self.pick_color)

    def update_color(self, color):
        self.color = color
        self.setStyleSheet(f"QPushButton#ColorSwatch {{ background-color: {color}; border: 2px solid #fff; border-radius: 20px; }}")

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.color), self, "Pick Color")
        if c.isValid():
            self.update_color(c.name())
            self.callback(c.name())

# -----------------------------------------------------------------------------
# WEB VIEWER SERVER
# -----------------------------------------------------------------------------
class WebViewerHandler(BaseHTTPRequestHandler):
    controller_instance = None
    
    def do_POST(self):
        c = WebViewerHandler.controller_instance
        if self.path == "/api/operator/command" and c:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                cmd = json.loads(post_data)
                action = cmd.get("action")
                
                if action == "play_pause": QTimer.singleShot(0, c.toggle_play)
                elif action == "reset": QTimer.singleShot(0, c.reset_timer)
                elif action == "next": QTimer.singleShot(0, c.play_next)
                elif action == "flash": QTimer.singleShot(0, c.trigger_flash_output)
                elif action == "blackout": QTimer.singleShot(0, lambda: c.toggle_blackout(not getattr(c.preview_display, 'is_blackout', False)))
                elif action == "nudge": 
                    val = cmd.get("value", 0)
                    QTimer.singleShot(0, lambda v=val: c.nudge_timer(v))
                elif action == "set_mode":
                    mode = cmd.get("mode")
                    QTimer.singleShot(0, lambda m=mode: c.set_current_timer_mode(m))
                elif action == "set_time":
                    secs = cmd.get("seconds", 0)
                    hhmm = cmd.get("hhmm", "12:00")
                    QTimer.singleShot(0, lambda s=secs, h=hhmm: c.set_current_timer_duration(s, h))
            except Exception as e:
                print(e)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/api/state":
            c = WebViewerHandler.controller_instance
            state_json = getattr(c, 'web_json_cache', '{}') if c else '{}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(state_json.encode('utf-8'))
            
        elif self.path == "/api/stream":
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            c = WebViewerHandler.controller_instance
            import time
            last_state = None
            while c:
                try:
                    state_json = getattr(c, 'web_json_cache', None)
                    if state_json and state_json != last_state:
                        self.wfile.write(b'data: ' + state_json.encode('utf-8') + b'\n\n')
                        self.wfile.flush()
                        last_state = state_json
                    time.sleep(0.1)
                except Exception:
                    break
            
        elif self.path == "/api/logo":
            c = WebViewerHandler.controller_instance
            if c and c.preview_display.settings.get('logo_path') and os.path.exists(c.preview_display.settings['logo_path']):
                try:
                    with open(c.preview_display.settings['logo_path'], 'rb') as f:
                        self.send_response(200)
                        self.send_header("Content-Type", "image/png")
                        self.send_header("Cache-Control", "no-cache")
                        self.end_headers()
                        self.wfile.write(f.read())
                except:
                    self.send_error(404)
            else:
                self.send_error(404)
            
        elif self.path == "/api/operator/state":
            c = WebViewerHandler.controller_instance
            state_json = getattr(c, 'op_json_cache', '{}') if c else '{}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(state_json.encode('utf-8'))
            
        elif self.path == "/api/operator/stream":
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            c = WebViewerHandler.controller_instance
            import time
            last_state = None
            while c:
                try:
                    state_json = getattr(c, 'op_json_cache', None)
                    if state_json and state_json != last_state:
                        self.wfile.write(b'data: ' + state_json.encode('utf-8') + b'\n\n')
                        self.wfile.flush()
                        last_state = state_json
                    time.sleep(0.1)
                except Exception:
                    break
            
        elif self.path == "/operator" or self.path == "/operator.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(OPERATOR_HTML.encode('utf-8'))
            
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
                <title>Timer Web Viewer</title>
                <style>
                    body, html { margin: 0; padding: 0; height: 100%; background: #000; color: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; overflow: hidden; }
                    #container { display: flex; flex-direction: column; height: 100%; justify-content: center; align-items: center; position: relative; }
                    #banner { display: flex; justify-content: space-between; align-items: center; position: absolute; top: 5vh; left: 5vw; width: 90vw; height: 12vh; }
                    #corner-logo { flex: 1; display: flex; justify-content: flex-start; align-items: center; height: 100%; }
                    #corner-logo img { max-height: 100%; max-width: 100%; object-fit: contain; }
                    #header { flex: 2; font-size: 8vh; color: #58a6ff; font-weight: bold; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 0; }
                    #corner-clock { flex: 1; display: flex; justify-content: flex-end; align-items: center; font-size: 5vh; font-weight: bold; }
                    #time { font-size: 45vh; font-weight: 800; text-align: center; line-height: 1; }
                    #message { display: none; position: absolute; bottom: 10%; width: 80%; background: rgba(20,20,20,0.95); color: #f6e05e; border: 2px solid #f6e05e; border-radius: 15px; padding: 15px; text-align: center; font-size: 6vh; font-weight: bold; }
                    #progress-container { position: absolute; bottom: 0; left: 0; width: 100%; height: 2vh; background: #333; }
                    #progress-bar { height: 100%; background: #48bb78; width: 0%; transition: width 0.5s; }
                    #blackout { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 10; }
                    #flash { display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: #fff; z-index: 11; }
                </style>
            </head>
            <body>
                <div id="container">
                    <div id="banner">
                        <div id="corner-logo"><img id="logo-img" style="display:none;" /></div>
                        <div id="header">Ready</div>
                        <div id="corner-clock"></div>
                    </div>
                    <div id="time">00:00</div>
                    <div id="message"></div>
                </div>
                <div id="progress-container"><div id="progress-bar"></div></div>
                <div id="blackout"></div>
                <div id="flash"></div>

                <script>
                    const logoImg = document.getElementById('logo-img');
                    logoImg.onerror = function() { this.style.display = 'none'; };
                
                    function poll() {
                        fetch('/api/state')
                        .then(r => r.json())
                        .then(d => {
                            document.body.style.backgroundColor = d.bg_color;
                            
                            document.getElementById('header').innerText = d.header;
                            document.getElementById('header').style.color = d.header_color;
                            
                            const clock = document.getElementById('corner-clock');
                            clock.innerText = d.clock_text;
                            clock.style.color = d.header_color;
                            clock.style.display = d.show_clock ? 'flex' : 'none';
                            
                            if (d.show_logo) {
                                logoImg.src = '/api/logo?t=' + Math.floor(Date.now() / 10000);
                                logoImg.style.display = 'block';
                            } else {
                                logoImg.style.display = 'none';
                            }
                            
                            document.getElementById('time').innerText = d.text;
                            document.getElementById('time').style.color = d.color;
                            document.getElementById('progress-bar').style.width = d.progress + '%';
                            document.getElementById('progress-bar').style.backgroundColor = d.progress >= 100 && parseInt(d.text.split(':')[0]) !== 0 ? '#da3633' : (d.progress_color || '#238636');
                            
                            const msg = document.getElementById('message');
                            if(d.message_visible) { msg.innerText = d.message; msg.style.display = 'block'; }
                            else { msg.style.display = 'none'; }
                            msg.style.color = d.message_color || '#f6e05e';
                            msg.style.borderColor = d.message_color || '#f6e05e';
                            
                            let align = d.timer_alignment || 'Center';
                            let justify = align === 'Left' ? 'flex-start' : (align === 'Right' ? 'flex-end' : 'center');
                            let txAlign = align === 'Left' ? 'left' : (align === 'Right' ? 'right' : 'center');
                            document.getElementById('container').style.alignItems = justify;
                            document.getElementById('time').style.textAlign = txAlign;
                            
                            let weightMap = {'Normal': 'normal', 'Bold': 'bold', 'Black': '900'};
                            document.getElementById('time').style.fontWeight = weightMap[d.font_weight || 'Bold'];
                            document.getElementById('header').style.fontWeight = weightMap[d.font_weight || 'Bold'];
                            clock.style.fontWeight = weightMap[d.font_weight || 'Bold'];

                            document.getElementById('blackout').style.display = d.blackout ? 'block' : 'none';
                            document.getElementById('flash').style.display = d.flash ? 'block' : 'none';
                        })
                        .catch(e => console.log('Error fetching state', e))
                        .finally(() => setTimeout(poll, 1000));
                    }
                    poll();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass # suppress console logging

class WebServerThread(QThread):
    def __init__(self, port=8080):
        super().__init__()
        self.port = port
        self.server = None
        
    def run(self):
        try:
            self.server = ThreadingHTTPServer(('', self.port), WebViewerHandler)
            logging.info(f"Web server started on port {self.port}")
            self.server.serve_forever()
        except OSError as e:
            logging.error(f"Failed to start web server on port {self.port}: {e}")
            
    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

# -----------------------------------------------------------------------------
# UNIFIED DISPLAY ENGINE
# -----------------------------------------------------------------------------
class TimerDisplay(QWidget):
    def __init__(self, parent=None, is_output=False):
        super().__init__(parent)
        self.is_output = is_output # Flag to know if this is the projector
        self.settings = DEFAULT_SETTINGS.copy()
        self.main_text = "00:00"
        self.header_text = "Ready"
        self.clock_text = "12:00 PM"
        self.progress_value = 0
        self.is_blackout = False
        self.message_text = ""
        self.is_message_visible = False
        
        # Timer Label (Background)
        self.timer_label = QLabel(self.main_text, self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Banner Frame (Foreground)
        self.banner_frame = QFrame(self)
        self.banner_layout = QHBoxLayout(self.banner_frame)
        self.banner_layout.setContentsMargins(40, 25, 40, 0)
        self.banner_layout.setSpacing(15)
        
        self.logo_label = QLabel()
        self.logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.logo_label.setVisible(False)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.title_block = QWidget()
        self.title_block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_layout = QVBoxLayout(self.title_block)
        self.title_layout.setContentsMargins(0,0,0,0)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        
        self.title_label = QLabel("")
        self.subtitle_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.subtitle_label)
        
        self.clock_label = QLabel(self.clock_text)
        self.clock_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.banner_layout.addWidget(self.logo_label, 1)
        self.banner_layout.addWidget(self.title_block, 2)
        self.banner_layout.addWidget(self.clock_label, 1)
        
        # Message Overlay
        self.msg_overlay = QLabel(self)
        self.msg_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_overlay.setWordWrap(True)
        self.msg_overlay.hide()
        
        # Blackout
        self.blackout_overlay = QWidget(self)
        self.blackout_overlay.setStyleSheet("background-color: black;")
        self.blackout_overlay.hide()
        
        # Flash Overlay
        self.flash_overlay = QWidget(self)
        self.flash_overlay.setStyleSheet("background-color: white;")
        self.flash_overlay.hide()
        
        # Progress
        self.progress_bar = QFrame(self)
        self.progress_bar.setStyleSheet("background-color: #333;")
        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setStyleSheet("background-color: #48bb78;")
        self.progress_fill.setGeometry(0, 0, 0, 16)
        
        # Enforce z-order
        self.banner_frame.raise_()
        self.msg_overlay.raise_()
        self.progress_bar.raise_()

        self.apply_design()

    def get_bool(self, key):
        val = self.settings.get(key, False)
        if isinstance(val, bool): return val
        return str(val).lower() in ('true', '1', 'yes', 'on')

    def trigger_flash(self):
        self.flash_overlay.show()
        self.flash_overlay.raise_()
        self.flash_overlay.resize(self.size())
        QTimer.singleShot(500, self.flash_overlay.hide)

    def update_state(self, timer_text, header_text, progress, is_overtime=False, remaining_secs=0):
        self.main_text = timer_text
        self.timer_label.setText(timer_text)
        self.header_text = header_text
        self.progress_value = progress
        
        # Preview now acts strictly as WYSIWYG for Output
        self.title_label.setText(header_text if header_text else "")
        self.subtitle_label.setVisible(False)

        self.clock_label.setText(QTime.currentTime().toString("h:mm AP"))
        
        use_smart = self.get_bool('smart_colors')
        override_color = None
        if use_smart:
            if is_overtime or remaining_secs <= 0:
                override_color = "#ff7b72" # Bright Red
            elif remaining_secs < 60:
                override_color = "#d29922" # Warning Yellow
            else:
                override_color = "#2ea043" # Success Green
        
        self.recalc_fonts(force_update_color=True, is_overtime=is_overtime, override_color=override_color)

        if self.get_bool('show_progress'):
            self.progress_bar.setVisible(True)
            width = self.progress_bar.width()
            fill_width = int(width * (min(max(progress, 0), 100) / 100))
            self.progress_fill.setFixedWidth(fill_width)
            if is_overtime or progress >= 100:
                self.progress_fill.setStyleSheet("background-color: #da3633;")
            else:
                prog_color = self.settings.get("progress_color", "#238636")
                self.progress_fill.setStyleSheet(f"background-color: {prog_color};")
        else:
            self.progress_bar.setVisible(False)

    def set_blackout(self, active):
        self.is_blackout = active
        self.blackout_overlay.setVisible(active)
        self.blackout_overlay.raise_()
        self.blackout_overlay.resize(self.size())

    def set_message(self, text, active, fullscreen=False):
        self.message_text = text
        self.is_message_visible = active
        self.is_message_fullscreen = fullscreen
        if active:
            self.msg_overlay.setText(text)
            self.msg_overlay.show()
            self.msg_overlay.raise_()
            self.recalc_fonts()
        else:
            self.msg_overlay.hide()

    def update_settings(self, new_settings):
        self.settings = new_settings
        self.apply_design()
        self.recalc_fonts()

    def apply_design(self):
        self.setObjectName("TimerDisplayScreen")
        bg_style = f"""
            #TimerDisplayScreen {{ background-color: {self.settings['bg_color']}; }}
            #TimerDisplayScreen QWidget {{ background-color: transparent; border: none; }}
            #TimerDisplayScreen QLabel {{ background-color: transparent; border: none; }}
        """
        self.setStyleSheet(bg_style)
        
        self.banner_frame.setObjectName("BannerFrame")
        self.banner_frame.setStyleSheet("#BannerFrame { background-color: transparent; }")
        
        self.clock_label.setVisible(self.get_bool('show_clock'))
        
        show_logo = self.get_bool('show_logo')
        has_logo = bool(show_logo and self.settings['logo_path'] and os.path.exists(self.settings['logo_path']))
        self.logo_label.setVisible(has_logo)
        self.update()

    def resizeEvent(self, event):
        self.recalc_fonts()
        if self.is_blackout: self.blackout_overlay.resize(self.size())
        if not self.flash_overlay.isHidden(): self.flash_overlay.resize(self.size())
        super().resizeEvent(event)

    def recalc_fonts(self, force_update_color=False, is_overtime=False, override_color=None):
        win_h = self.height()
        win_w = self.width()
        if win_h < 100: win_h = 100
        
        prog_h = max(8, int(win_h * 0.015))
        self.progress_bar.setGeometry(0, win_h - prog_h, win_w, prog_h)
        self.progress_fill.setFixedHeight(prog_h)
        fill_width = int(win_w * (min(max(self.progress_value, 0), 100) / 100))
        self.progress_fill.setFixedWidth(fill_width)

        banner_h = int(win_h * 0.15)
        self.banner_frame.setGeometry(0, 0, win_w, banner_h)
        self.timer_label.setGeometry(0, 0, win_w, win_h)

        timer_size = int(win_h * 0.55 * (self.settings['scale_timer'] / 100.0))
        header_size = int(win_h * 0.08 * (self.settings['scale_header'] / 100.0))
        subtitle_size = int(max(10, header_size * 0.6))
        font_family = self.settings['font_family']
        font_weight = self.settings.get('font_weight', 'Bold')
        weight_css = "bold" if font_weight == "Bold" else ("900" if font_weight == "Black" else "normal")
        timer_alignment = self.settings.get('timer_alignment', 'Center')
        t_color = self.settings['text_color']
        if override_color: t_color = override_color
        elif is_overtime: t_color = "#fc8181"
        self.current_timer_color = t_color

        q_align = Qt.AlignmentFlag.AlignCenter
        if timer_alignment == "Left": q_align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif timer_alignment == "Right": q_align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        self.timer_label.setAlignment(q_align)
            
        self.timer_label.setStyleSheet(f"font-family: '{font_family}'; font-size: {max(6, timer_size)}px; font-weight: {weight_css}; color: {t_color}; border: none; background-color: transparent;")
        self.title_label.setStyleSheet(f"font-family: '{font_family}'; font-size: {max(6, header_size)}px; color: {self.settings['header_color']}; border: none; font-weight: {weight_css};")
        self.clock_label.setStyleSheet(f"font-family: '{font_family}'; font-size: {max(6, header_size)}px; color: {self.settings['header_color']}; border: none; font-weight: {weight_css};")
        self.subtitle_label.setStyleSheet(f"font-family: '{font_family}'; font-size: {subtitle_size}px; color: #888; font-style: italic;")
        
        if self.is_message_visible:
            msg_color = self.settings.get("message_color", "#f6e05e")
            if getattr(self, 'is_message_fullscreen', False):
                self.msg_overlay.setGeometry(0, 0, win_w, win_h)
                msg_full_size = int(win_h * 0.12)
                self.msg_overlay.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.90); color: {msg_color}; font-weight: bold; font-size: {max(24, msg_full_size)}px; font-family: '{font_family}'; padding: 40px; border: none; border-radius: 0px;")
            else:
                box_w = int(win_w * 0.8)
                box_h = int(win_h * 0.3)
                box_x = (win_w - box_w) // 2
                box_y = win_h - box_h - int(win_h * 0.05)
                self.msg_overlay.setGeometry(box_x, box_y, box_w, box_h)
                msg_font_size = int(win_h * 0.08)
                self.msg_overlay.setStyleSheet(f"background-color: rgba(20, 20, 20, 0.95); color: {msg_color}; font-weight: bold; font-size: {max(12, msg_font_size)}px; font-family: '{font_family}'; border: 2px solid {msg_color}; border-radius: 15px; padding: 10px;")
        
        if self.logo_label.isVisible() and self.settings['logo_path']:
            target_h = int(win_h * 0.20 * (self.settings['scale_logo'] / 100.0))
            pix = QPixmap(self.settings['logo_path'])
            if not pix.isNull():
                self.logo_label.setPixmap(pix.scaledToHeight(max(10, target_h), Qt.TransformationMode.SmoothTransformation))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.settings['bg_image_path'] and os.path.exists(self.settings['bg_image_path']):
            painter = QPainter(self)
            pix = QPixmap(self.settings['bg_image_path'])
            mode = self.settings['bg_mode']
            if mode == "Stretch": painter.drawPixmap(self.rect(), pix)
            elif mode == "Fit":
                scaled = pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                scaled = pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)

class ProjectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timer - Output")
        # Pass is_output=True to handle clean display logic
        self.display = TimerDisplay(is_output=True)
        self.setCentralWidget(self.display)
        self.resize(800, 450)
        self.setWindowFlags(Qt.WindowType.Window)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11: self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape: self.showNormal()
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.toggle_fullscreen()
    def toggle_fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()

# -----------------------------------------------------------------------------
# RUN SHEET ROW
# -----------------------------------------------------------------------------
class TimerRowWidget(QFrame):
    delete_clicked = pyqtSignal()
    play_clicked = pyqtSignal()
    data_changed = pyqtSignal()

    DEFAULT_STYLE = """
        QFrame#Panel {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
        }
        QFrame#Panel:hover {
            border: 1px solid #8b949e;
        }
        QComboBox {
            background: transparent;
            border: 1px solid transparent;
            color: #58a6ff;
            font-weight: 600;
            font-size: 14px;
            padding: 4px 8px;
            border-radius: 4px;
        }
        QComboBox:hover { background: #21262d; border: 1px solid #30363d; }
        QComboBox::drop-down { border: none; width: 0px; }
        QSpinBox, QTimeEdit {
            background: transparent;
            border: 1px solid transparent;
            font-size: 18px;
            font-weight: 800;
            color: #ffffff;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QSpinBox:hover, QTimeEdit:hover { background: #21262d; }
        QSpinBox::up-button, QTimeEdit::up-button, QSpinBox::down-button, QTimeEdit::down-button {
            width: 0px; border: none;
        }
        QLineEdit {
            background: transparent;
            border: 1px solid transparent;
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            padding: 4px 8px;
            border-radius: 4px;
        }
        QLineEdit:hover { background: #21262d; }
        QLineEdit:focus { border: 1px solid #58a6ff; background: #0d1117; }
    """

    PLAYING_STYLE = """
        QFrame#Panel {
            background-color: #1f6feb;
            border: 1px solid #388bfd;
            border-radius: 8px;
        }
        QLineEdit, QSpinBox, QTimeEdit { color: white; font-weight: bold; background: transparent; border: none; }
        QSpinBox::up-button, QTimeEdit::up-button, QSpinBox::down-button, QTimeEdit::down-button { width: 0px; border: none; }
        QComboBox { color: rgba(255, 255, 255, 0.9); background: transparent; border: none; }
        QComboBox::drop-down { border: none; width: 0px; }
        QLabel { color: white; }
    """

    def __init__(self, data):
        super().__init__()
        self.setObjectName("Panel")
        self.data = data 
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(15)
        
        self.setStyleSheet(self.DEFAULT_STYLE)
        
        # 1. Color Indicator (Left-most, thin strip)
        self.color_indicator = QPushButton()
        self.color_indicator.setFixedSize(12, 36)
        self.current_label_color = data.get("label_color", "transparent")
        self._set_indicator_color(self.current_label_color)
        self.color_indicator.setToolTip("Right-click to clear, Left-click to set color")
        self.color_indicator.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.color_indicator.customContextMenuRequested.connect(self.clear_label_color)
        self.color_indicator.clicked.connect(self.pick_label_color)
        self.layout.addWidget(self.color_indicator)
        
        # 2. Mode (Combo Box - visually subtle like a subtitle)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([TimerMode.COUNTDOWN, TimerMode.COUNTUP, TimerMode.FINISH_AT, TimerMode.TOD])
        self.mode_combo.setCurrentText(data.get("mode", TimerMode.COUNTDOWN))
        self.mode_combo.setMinimumWidth(110)
        self.mode_combo.currentTextChanged.connect(self.on_mode_change)
        self.layout.addWidget(self.mode_combo)
        
        # 3. Time input (Stacked - prominently bold)
        self.stack = QStackedWidget()
        self.stack.setFixedWidth(80)
        
        self.spin_mins = QSpinBox()
        self.spin_mins.setRange(0, 999)
        self.spin_mins.setSuffix("m")
        self.spin_mins.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_mins.setValue(data.get("duration_mins", 10))
        self.spin_mins.valueChanged.connect(self.on_change)
        self.stack.addWidget(self.spin_mins)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_str = data.get("target_time", "12:00")
        self.time_edit.setTime(QTime.fromString(t_str, "HH:mm"))
        self.time_edit.timeChanged.connect(self.on_change)
        self.stack.addWidget(self.time_edit)
        
        self.no_input = QLabel("--:--")
        self.no_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_input.setStyleSheet("color: #8b949e; font-size: 18px; font-weight: 800;")
        self.stack.addWidget(self.no_input)
        
        self.layout.addWidget(self.stack)
        self.update_input_visibility()
        
        # 4. Title (Expanding)
        self.title_edit = QLineEdit(data.get("title", "New Timer"))
        self.title_edit.setPlaceholderText("Event Title")
        self.title_edit.textChanged.connect(self.on_change)
        self.layout.addWidget(self.title_edit, 1)
        
        # 5. Buttons (Right aligned group)
        self.btn_style = "QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; color: #c9d1d9; font-weight: bold; } QPushButton:hover { background-color: #30363d; }"
        
        self.play_btn = QPushButton("⏵")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setCheckable(True)
        self.play_btn.setStyleSheet(f"{self.btn_style} QPushButton {{ color: #3fb950; font-size: 20px; }}")
        self.play_btn.clicked.connect(self.play_clicked.emit)
        self.layout.addWidget(self.play_btn)

        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(40, 40)
        self.del_btn.setStyleSheet(f"{self.btn_style} QPushButton:hover {{ background-color: #da3633; color: white; border-color: #da3633; }}")
        self.del_btn.clicked.connect(self.delete_clicked.emit)
        self.layout.addWidget(self.del_btn)

    def _set_indicator_color(self, color_str):
        if color_str == "transparent" or not color_str:
            self.color_indicator.setStyleSheet("background-color: transparent; border: 1px dashed #555; border-radius: 6px;")
        else:
            self.color_indicator.setStyleSheet(f"background-color: {color_str}; border: none; border-radius: 6px;")

    def pick_label_color(self):
        initial = QColor(self.current_label_color) if self.current_label_color not in ["transparent", ""] else QColor("#30363d")
        c = QColorDialog.getColor(initial, self, "Pick Label Color")
        if c.isValid():
            self.current_label_color = c.name()
            self.data["label_color"] = self.current_label_color
            self._set_indicator_color(self.current_label_color)
            self.data_changed.emit()

    def clear_label_color(self, pos):
        self.current_label_color = "transparent"
        self.data["label_color"] = "transparent"
        self._set_indicator_color("transparent")
        self.data_changed.emit()

    def on_mode_change(self):
        self.data["mode"] = self.mode_combo.currentText()
        self.update_input_visibility()
        self.on_change()

    def update_input_visibility(self):
        m = self.data["mode"]
        if m == TimerMode.FINISH_AT: self.stack.setCurrentWidget(self.time_edit)
        elif m == TimerMode.TOD: self.stack.setCurrentWidget(self.no_input)
        else: self.stack.setCurrentWidget(self.spin_mins)

    def on_change(self):
        self.data["title"] = self.title_edit.text()
        self.data["duration_mins"] = self.spin_mins.value()
        self.data["target_time"] = self.time_edit.time().toString("HH:mm")
        self.data_changed.emit()

    def set_playing(self, is_playing):
        self.play_btn.setChecked(is_playing)
        if is_playing:
            self.play_btn.setText("⏸")
            self.play_btn.setStyleSheet("QPushButton { background-color: #0d1117; border: 1px solid transparent; border-radius: 8px; font-size: 18px; color: #f85149; font-weight: bold; }")
            self.del_btn.setStyleSheet("QPushButton { background-color: #0d1117; border: 1px solid transparent; border-radius: 8px; font-size: 16px; color: #c9d1d9; font-weight: bold; } QPushButton:hover { background-color: #da3633; color: white; border-color: #da3633; }")
            self.setStyleSheet(self.PLAYING_STYLE)
        else:
            self.play_btn.setText("⏵")
            self.play_btn.setStyleSheet(f"{self.btn_style} QPushButton {{ color: #3fb950; font-size: 20px; }}")
            self.del_btn.setStyleSheet(f"{self.btn_style} QPushButton:hover {{ background-color: #da3633; color: white; border-color: #da3633; }}")
            self.setStyleSheet(self.DEFAULT_STYLE)


# -----------------------------------------------------------------------------
# MAIN CONTROLLER
# -----------------------------------------------------------------------------
class ControllerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # BRANDING UPDATE
        self.setWindowTitle(f"{APP_NAME} - Controller")
        self.resize(1280, 850)
        self.projector = ProjectorWindow()
        # REMOVE AUTO SHOW: self.projector.show() 
        self.timer_logic = QTimer()
        self.timer_logic.timeout.connect(self.tick)
        self.timer_logic.start(100) 
        self.current_timer_data = None 
        self.start_time = None
        self.pause_time = None
        self.is_running = False
        self.elapsed_paused = 0 
        self.has_flashed_zero = False
        self.run_sheet_data = []

        self.web_json_cache = "{}"
        self.op_json_cache = "{}"

        WebViewerHandler.controller_instance = self
        self.web_server = WebServerThread(port=8080)
        self.web_server.start()

        self.init_ui()
        self.load_data()

    def init_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        save_action = QAction("Save Template...", self)
        save_action.triggered.connect(self.save_template)
        file_menu.addAction(save_action)
        
        load_action = QAction("Open Template...", self)
        load_action.triggered.connect(self.load_template)
        file_menu.addAction(load_action)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # === LEFT COLUMN ===
        left_col = QVBoxLayout()
        left_col.setSpacing(15)
        # BRANDING UPDATE
        left_col.addWidget(QLabel(f"{APP_NAME} ({SUBTITLE})", objectName="SectionHeader"))
        
        # 1. Live Output
        preview_grp = QGroupBox("Live Output")
        preview_layout = QVBoxLayout(preview_grp)
        preview_layout.setContentsMargins(5, 20, 5, 5)
        self.preview_display = TimerDisplay()
        self.preview_wrapper = AspectRatioWidget(self.preview_display, ratio=16/9)
        self.preview_wrapper.setMinimumHeight(180) 
        preview_layout.addWidget(self.preview_wrapper)
        left_col.addWidget(preview_grp, 2) 
        
        # 2. Operator Clocks
        clock_frame = QFrame(objectName="Panel")
        clock_layout = QHBoxLayout(clock_frame)
        
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("CURRENT TIME", objectName="InfoLabel"))
        self.op_clock_label = QLabel("--:--:--", objectName="InfoValue")
        v1.addWidget(self.op_clock_label)
        clock_layout.addLayout(v1)
        
        v2 = QVBoxLayout()
        v2.addWidget(QLabel("PROJECTED END", objectName="InfoLabel"))
        self.op_end_label = QLabel("--:--:--", objectName="InfoValue")
        self.op_end_label.setStyleSheet("color: #48bb78;") 
        v2.addWidget(self.op_end_label)
        clock_layout.addLayout(v2)
        left_col.addWidget(clock_frame)

        # 3. Transport
        transport_frame = QFrame(objectName="Panel")
        trans_layout = QVBoxLayout(transport_frame)
        trans_layout.setContentsMargins(24, 24, 24, 24)
        trans_layout.setSpacing(16)
        
        self.start_btn = QPushButton("START TIMER")
        self.start_btn.setObjectName("PrimaryBtn")
        self.start_btn.setMinimumHeight(64)
        self.start_btn.setCheckable(True)
        self.start_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.start_btn.clicked.connect(self.toggle_play)
        trans_layout.addWidget(self.start_btn)
        
        nudge_grid = QGridLayout()
        nudge_grid.setSpacing(10)
        nudge_vals = [("-1m", -60), ("-30s", -30), ("+30s", 30), ("+1m", 60)]
        for i, (label, val) in enumerate(nudge_vals):
            btn = QPushButton(label)
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _, v=val: self.nudge_timer(v))
            nudge_grid.addWidget(btn, 0, i)
        trans_layout.addLayout(nudge_grid)
        
        self.reset_btn = QPushButton("RESET TIMER")
        self.reset_btn.setMinimumHeight(44)
        self.reset_btn.clicked.connect(self.reset_timer)
        trans_layout.addWidget(self.reset_btn)
        
        self.next_btn = QPushButton("NEXT TIMER")
        self.next_btn.setMinimumHeight(44)
        self.next_btn.clicked.connect(self.play_next)
        trans_layout.addWidget(self.next_btn)
        
        left_col.addWidget(transport_frame)
        
        # === RIGHT COLUMN (Tabs) ===
        self.tabs = QTabWidget()
        
        # Tab 1: Run Sheet
        run_tab = QWidget()
        run_layout = QVBoxLayout(run_tab)
        run_layout.setSpacing(15)
        
        run_header = QHBoxLayout()
        run_header.addWidget(QLabel("Timers", objectName="SectionHeader"))
        run_header.addStretch()
        add_btn = QPushButton("+ Add Timer")
        add_btn.setObjectName("PrimaryBtn")
        add_btn.clicked.connect(self.add_timer_row)
        run_header.addWidget(add_btn)
        run_layout.addLayout(run_header)
        
        self.run_list = QListWidget()
        self.run_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.run_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.run_list.model().rowsMoved.connect(self.on_rows_moved)
        run_layout.addWidget(self.run_list)
        
        msg_frame = QFrame(objectName="Panel")
        msg_layout = QVBoxLayout(msg_frame)
        msg_layout.addWidget(QLabel("Messages & Tools", objectName="SectionHeader"))
        
        msg_row = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Enter message...")
        self.msg_input.textChanged.connect(self.update_message)
        
        self.msg_full_chk = QCheckBox("Fullscreen")
        self.msg_full_chk.toggled.connect(self.update_message)
        
        self.msg_btn = QPushButton("Show")
        self.msg_btn.setCheckable(True)
        self.msg_btn.toggled.connect(self.toggle_message)
        
        msg_row.addWidget(self.msg_input)
        msg_row.addWidget(self.msg_full_chk)
        msg_row.addWidget(self.msg_btn)
        msg_layout.addLayout(msg_row)
        
        quick_msg_row = QHBoxLayout()
        quick_msg_row.setSpacing(5)
        for qm in ["Wrap Up", "Q & A Time", "Clear Stage"]:
            qbtn = QPushButton(qm)
            qbtn.clicked.connect(lambda _, m=qm: self.set_quick_message(m))
            quick_msg_row.addWidget(qbtn)
        msg_layout.addLayout(quick_msg_row)
        
        tools_row = QHBoxLayout()
        self.blackout_btn = QPushButton("Blackout")
        self.blackout_btn.setCheckable(True)
        self.blackout_btn.toggled.connect(self.toggle_blackout)
        
        self.flash_btn = QPushButton("FLASH")
        self.flash_btn.clicked.connect(self.trigger_flash_output)
        
        self.open_output_btn = QPushButton("Open Output")
        self.open_output_btn.clicked.connect(self.open_output_window)
        
        self.fullscreen_btn = QPushButton("Full")
        self.fullscreen_btn.clicked.connect(self.toggle_projector_fullscreen)
        
        tools_row.addWidget(self.blackout_btn)
        tools_row.addWidget(self.flash_btn)
        tools_row.addWidget(self.open_output_btn)
        tools_row.addWidget(self.fullscreen_btn)
        msg_layout.addLayout(tools_row)
        
        run_layout.addWidget(msg_frame)
        self.tabs.addTab(run_tab, "Run Sheet")
        
        # Tab 2: Design - NEW GRID LAYOUT
        design_tab = QWidget()
        d_main = QVBoxLayout(design_tab)
        
        d_scroll = QScrollArea()
        d_scroll.setWidgetResizable(True)
        d_scroll.setStyleSheet("background: transparent; border: none;")
        
        d_content = QWidget()
        d_grid = QGridLayout(d_content)
        d_grid.setSpacing(25)
        d_grid.setColumnStretch(0, 1)
        d_grid.setColumnStretch(1, 1)
        
        # 1. Typography & Scale (Col 0, Row 0)
        font_grp = QGroupBox("Typography && Scale")
        f_layout = QFormLayout(font_grp)
        f_layout.setVerticalSpacing(15)
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.update_design_from_ui)
        f_layout.addRow("Font Family:", self.font_combo)
        
        self.weight_combo = QComboBox()
        self.weight_combo.addItems(["Normal", "Bold", "Black"])
        self.weight_combo.currentTextChanged.connect(self.update_design_from_ui)
        f_layout.addRow("Font Weight:", self.weight_combo)
        
        self.align_combo = QComboBox()
        self.align_combo.addItems(["Left", "Center", "Right"])
        self.align_combo.currentTextChanged.connect(self.update_design_from_ui)
        f_layout.addRow("Timer Align:", self.align_combo)
        
        self.create_slider(f_layout, "Timer Scale", "scale_timer", 50, 200)
        self.create_slider(f_layout, "Header Scale", "scale_header", 50, 200)
        d_grid.addWidget(font_grp, 0, 0)
        
        # 2. Background & Logos (Col 1, Row 0)
        bg_grp = QGroupBox("Background & Assets")
        bg_layout = QVBoxLayout(bg_grp)
        bg_layout.setSpacing(15)
        self.create_file_picker_vbox(bg_layout, "Background Image:", "bg_image_path")
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems(["Cover", "Fit", "Stretch"])
        self.bg_mode_combo.currentTextChanged.connect(self.update_design_from_ui)
        bg_layout.addWidget(self.bg_mode_combo)
        self.create_file_picker_vbox(bg_layout, "Logo Image:", "logo_path")
        self.create_slider_vbox(bg_layout, "Logo Scale", "scale_logo", 10, 200)
        d_grid.addWidget(bg_grp, 0, 1)
        
        # 3. Colors (Col 0, Row 1)
        color_grp = QGroupBox("Theme Colors")
        cg_layout = QGridLayout(color_grp)
        cg_layout.setSpacing(15)
        colors = [
            ("Background", "bg_color"), ("Main Text", "text_color"), 
            ("Header Text", "header_color"), ("Progress Bar", "progress_color"), 
            ("Message Text", "message_color")
        ]
        for i, (lbl, key) in enumerate(colors):
            r, c = divmod(i, 3) 
            vbox = QVBoxLayout()
            vbox.addWidget(QLabel(lbl), 0, Qt.AlignmentFlag.AlignCenter)
            swatch = ColorSwatch(self.preview_display.settings.get(key, "#ffffff"), lambda c, k=key: self.update_color_setting(k, c))
            vbox.addWidget(swatch, 0, Qt.AlignmentFlag.AlignCenter)
            cg_layout.addLayout(vbox, r, c)
        d_grid.addWidget(color_grp, 1, 0)
        
        # 4. Visibility (Col 1, Row 1)
        vis_grp = QGroupBox("Visibility Options")
        vis_layout = QVBoxLayout(vis_grp)
        vis_layout.setSpacing(15)
        self.chk_clock = QCheckBox("Show Real-Time Clock")
        self.chk_logo = QCheckBox("Show Logo")
        self.chk_prog = QCheckBox("Show Progress Bar")
        self.chk_smart = QCheckBox("Smart Traffic Light Colors")
        self.chk_overtime = QCheckBox("Allow Overtime (count up from 0)")
        self.chk_advance = QCheckBox("Auto-Advance to next timer")
        
        for chk, key in [(self.chk_clock, 'show_clock'), (self.chk_logo, 'show_logo'), 
                         (self.chk_prog, 'show_progress'), (self.chk_smart, 'smart_colors'),
                         (self.chk_overtime, 'allow_overtime'), (self.chk_advance, 'auto_advance')]:
            chk.toggled.connect(self.update_design_from_ui)
            vis_layout.addWidget(chk)
            
        vis_layout.addStretch()
        
        web_info_layout = QVBoxLayout()
        web_info_layout.addWidget(QLabel("Web Viewer URL:"))
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except:
            ip = "127.0.0.1"
            
        web_url = QLineEdit(f"http://{ip}:8080")
        web_url.setReadOnly(True)
        web_info_layout.addWidget(web_url)
        vis_layout.addLayout(web_info_layout)
        
        d_grid.addWidget(vis_grp, 1, 1)
        
        # Finish Design Tab
        d_scroll.setWidget(d_content)
        d_main.addWidget(d_scroll)
        self.tabs.addTab(design_tab, "Design")
        
        main_layout.addLayout(left_col, 4)
        main_layout.addWidget(self.tabs, 6)

    def open_output_window(self):
        self.projector.show()
        self.projector.raise_()
        self.projector.activateWindow()
        self.projector.showNormal() 

    def toggle_projector_fullscreen(self):
        self.projector.toggle_fullscreen()

    def set_quick_message(self, msg):
        self.msg_input.setText(msg)
        self.msg_btn.setChecked(True)
        self.update_message()

    def play_next(self):
        if not self.run_sheet_data: return
        if not self.current_timer_data:
            first_item = self.run_list.item(0)
            if first_item:
                w = self.run_list.itemWidget(first_item)
                if w: self.play_row(w, w.data)
            return
            
        try:
            current_idx = self.run_sheet_data.index(self.current_timer_data)
            next_idx = current_idx + 1
            if next_idx < len(self.run_sheet_data):
                next_item = self.run_list.item(next_idx)
                if next_item:
                    w = self.run_list.itemWidget(next_item)
                    if w: self.play_row(w, w.data)
        except ValueError:
            pass

    def save_template(self):
        f, _ = QFileDialog.getSaveFileName(self, "Save Template", "", "NTE Templates (*.nte)")
        if f:
            if not f.endswith('.nte'): f += '.nte'
            data = {"run_sheet": self.run_sheet_data, "settings": self.preview_display.settings}
            try:
                with open(f, 'w') as out: json.dump(data, out)
            except Exception as e: print(e)

    def load_template(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open Template", "", "NTE Templates (*.nte)")
        if f:
            try:
                with open(f, 'r') as inh: data = json.load(inh)
                self.run_sheet_data = []
                self.run_list.clear() # clear visually
                self.current_timer_data = None
                self.reset_timer_logic()
                for row in data.get("run_sheet", []): self.add_timer_row(row)
                
                new_settings = data.get("settings", {})
                for k, v in new_settings.items():
                    if k in self.preview_display.settings:
                        self.preview_display.settings[k] = v
                
                s = self.preview_display.settings
                self.chk_logo.setChecked(bool(s.get('show_logo', False)))
                self.chk_clock.setChecked(bool(s.get('show_clock', False)))
                self.chk_prog.setChecked(bool(s.get('show_progress', False)))
                self.chk_smart.setChecked(bool(s.get('smart_colors', False)))
                self.chk_overtime.setChecked(bool(s.get('allow_overtime', False)))
                self.chk_advance.setChecked(bool(s.get('auto_advance', False)))
                self.font_combo.setCurrentFont(QFont(s.get('font_family', 'Arial')))
                if hasattr(self, 'weight_combo'): self.weight_combo.setCurrentText(s.get('font_weight', 'Bold'))
                if hasattr(self, 'align_combo'): self.align_combo.setCurrentText(s.get('timer_alignment', 'Center'))
                self.bg_mode_combo.setCurrentText(s.get('bg_mode', 'Cover'))
                self.sync_design_to_projector()
            except Exception as e: print(e)
            
    def trigger_flash_output(self):
        self.projector.display.trigger_flash()
        self.preview_display.trigger_flash()

    def on_rows_moved(self, parent, start, end, dest, row):
        # Smart Save: Reconstruct data list from visual list items
        new_data = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            widget = self.run_list.itemWidget(item)
            if widget:
                new_data.append(widget.data)
        self.run_sheet_data = new_data
        self.save_data()

    # --- Helpers ---
    def update_color_setting(self, key, color):
        self.preview_display.settings[key] = color
        self.sync_design_to_projector()

    def create_slider(self, layout, label, key, min_v, max_v):
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(min_v, max_v)
        sl.setValue(DEFAULT_SETTINGS[key])
        sl.valueChanged.connect(lambda v: self.on_slider_change(key, v))
        layout.addRow(label, sl)

    def create_slider_vbox(self, layout, label, key, min_v, max_v):
        l = QHBoxLayout()
        l.addWidget(QLabel(label))
        sl = QSlider(Qt.Orientation.Horizontal)
        sl.setRange(min_v, max_v)
        sl.setValue(DEFAULT_SETTINGS[key])
        sl.valueChanged.connect(lambda v: self.on_slider_change(key, v))
        l.addWidget(sl)
        layout.addLayout(l)

    def create_file_picker(self, layout, label, key):
        # NOT USED IN V17.13 but kept for compatibility
        self.create_file_picker_vbox(layout, label, key)
        
    def create_file_picker_vbox(self, layout, label, key):
        l_wrap = QVBoxLayout()
        l_wrap.setSpacing(5)
        l_wrap.addWidget(QLabel(label))
        
        path_edit = QLineEdit()
        path_edit.setReadOnly(True)
        path_edit.setText(self.preview_display.settings[key])
        path_edit.setStyleSheet("color: #888;") # Dim text to focus on buttons
        l_wrap.addWidget(path_edit)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        # Large Choose Button
        btn_choose = QPushButton("Choose Image")
        btn_choose.setObjectName("FileBtn")
        btn_choose.setMinimumHeight(35)
        btn_choose.clicked.connect(lambda: self.pick_file(key, path_edit))
        
        # Large Remove Button
        btn_remove = QPushButton("Remove")
        btn_remove.setObjectName("RemoveBtn")
        btn_remove.setMinimumHeight(35)
        btn_remove.clicked.connect(lambda: self.clear_file(key, path_edit))
        
        btn_row.addWidget(btn_choose)
        btn_row.addWidget(btn_remove)
        
        l_wrap.addLayout(btn_row)
        layout.addLayout(l_wrap)

    def pick_file(self, key, widget):
        f, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if f:
            widget.setText(f)
            self.preview_display.settings[key] = f
            self.sync_design_to_projector()

    def clear_file(self, key, widget):
        widget.setText("")
        self.preview_display.settings[key] = ""
        self.sync_design_to_projector()

    def on_slider_change(self, key, val):
        self.preview_display.settings[key] = val
        self.sync_design_to_projector()

    def update_design_from_ui(self):
        s = self.preview_display.settings
        s['font_family'] = self.font_combo.currentFont().family()
        if hasattr(self, 'weight_combo'): s['font_weight'] = self.weight_combo.currentText()
        if hasattr(self, 'align_combo'): s['timer_alignment'] = self.align_combo.currentText()
        s['bg_mode'] = self.bg_mode_combo.currentText()
        s['show_logo'] = self.chk_logo.isChecked()
        s['show_clock'] = self.chk_clock.isChecked()
        s['show_progress'] = self.chk_prog.isChecked()
        s['smart_colors'] = self.chk_smart.isChecked()
        s['allow_overtime'] = self.chk_overtime.isChecked()
        s['auto_advance'] = self.chk_advance.isChecked()
        self.sync_design_to_projector()

    def sync_design_to_projector(self):
        self.preview_display.update_settings(self.preview_display.settings)
        self.projector.display.update_settings(self.preview_display.settings)
        self.save_settings()

    # --- Logic ---
    def add_timer_row(self, data=None):
        if not data: data = {"title": "", "mode": TimerMode.COUNTDOWN, "duration_mins": 10, "target_time": "12:00"}
        self.run_sheet_data.append(data)
        item = QListWidgetItem(self.run_list)
        item.setSizeHint(QSize(100, 80))
        widget = TimerRowWidget(data)
        widget.delete_clicked.connect(lambda: self.delete_row(item, data))
        widget.play_clicked.connect(lambda: self.play_row(widget, data))
        widget.data_changed.connect(self.save_data)
        self.run_list.setItemWidget(item, widget)
        self.save_data()

    def delete_row(self, item, data):
        row = self.run_list.row(item)
        self.run_list.takeItem(row)
        if data in self.run_sheet_data: self.run_sheet_data.remove(data)
        if self.current_timer_data == data:
            self.reset_timer()
            self.current_timer_data = None
        self.save_data()

    def play_row(self, widget, data):
        for i in range(self.run_list.count()):
            it = self.run_list.item(i)
            w = self.run_list.itemWidget(it)
            if w: w.set_playing(False)
        self.current_timer_data = data
        widget.set_playing(True)
        self.reset_timer_logic()
        self.update_display_text()

    def toggle_play(self):
        if not self.current_timer_data: return
        if self.is_running:
            self.is_running = False
            self.start_btn.setText("START TIMER")
            self.start_btn.setChecked(False)
            self.pause_time = datetime.now()
        else:
            self.is_running = True
            self.start_btn.setText("PAUSE")
            self.start_btn.setChecked(True)
            if self.start_time is None: self.start_time = datetime.now()
            elif self.pause_time:
                self.start_time += (datetime.now() - self.pause_time)
                self.pause_time = None

    def reset_timer(self):
        self.is_running = False
        self.start_btn.setText("START TIMER")
        self.start_btn.setChecked(False)
        self.reset_timer_logic()
        self.update_display_text()

    def reset_timer_logic(self):
        self.start_time = None
        self.pause_time = None
        self.elapsed_paused = 0
        self.has_flashed_zero = False

    def nudge_timer(self, seconds):
        if not self.start_time: return
        self.start_time += timedelta(seconds=seconds)
        self.tick()

    def toggle_blackout(self, active):
        self.preview_display.set_blackout(active)
        self.projector.display.set_blackout(active)
        self.blackout_btn.setStyleSheet("background-color: #cf222e; color: white; border: none;" if active else "")

    def toggle_message(self, active):
        self.msg_btn.setText("Hide" if active else "Show")
        self.msg_btn.setStyleSheet("background-color: #e0e0e0; color: #121212;" if active else "")
        self.update_message()

    def update_message(self, *_):
        active = self.msg_btn.isChecked()
        txt = self.msg_input.text()
        fullscreen = getattr(self, 'msg_full_chk', None) and self.msg_full_chk.isChecked()
        self.preview_display.set_message(txt, active, fullscreen)
        self.projector.display.set_message(txt, active, fullscreen)

    def toggle_fullscreen(self):
        self.projector.toggle_fullscreen()

    def get_current_row_widget(self):
        if not self.current_timer_data: return None
        for i in range(self.run_list.count()):
            it = self.run_list.item(i)
            w = self.run_list.itemWidget(it)
            if w and w.data == self.current_timer_data:
                return w
        return None

    def set_current_timer_mode(self, mode):
        w = self.get_current_row_widget()
        if w:
            w.mode_combo.setCurrentText(mode)

    def set_current_timer_duration(self, seconds, hhmm):
        w = self.get_current_row_widget()
        if w:
            mode = w.mode_combo.currentText()
            if mode in [TimerMode.FINISH_AT, TimerMode.TOD]:
                w.time_edit.setTime(QTime.fromString(hhmm, "HH:mm"))
            else:
                w.spin_mins.setValue(max(0, seconds // 60))
        
        # We also need to reset the active run logic if it's currently running, so it applies immediately.
        if self.current_timer_data and not self.is_running:
            # Updating the timer logic visually when paused
            self.reset_timer_logic()
            self.update_display_text()

    def tick(self):
        # Update operator clocks
        now = datetime.now()
        self.op_clock_label.setText(now.strftime("%H:%M:%S"))
        
        # Calculate End Time and Remaining for Logic
        end_str = "--:--:--"
        remaining_secs = 0
        
        if self.current_timer_data:
            mode = self.current_timer_data['mode']
            if mode == TimerMode.COUNTDOWN:
                duration = self.current_timer_data['duration_mins'] * 60
                if self.start_time:
                    if self.is_running:
                        end_time = self.start_time + timedelta(seconds=duration)
                        remaining_secs = (end_time - now).total_seconds()
                        if remaining_secs <= 0:
                            if not self.preview_display.settings.get('allow_overtime', False):
                                self.is_running = False
                                self.start_btn.setText("START TIMER")
                                self.start_btn.setChecked(False)
                                self.pause_time = end_time
                                remaining_secs = 0
                                if not self.has_flashed_zero:
                                    self.trigger_flash_output()
                                    self.has_flashed_zero = True
                                    if self.preview_display.settings.get('auto_advance', False):
                                        QTimer.singleShot(600, self.play_next)
                            else:
                                if not self.has_flashed_zero:
                                    self.trigger_flash_output()
                                    self.has_flashed_zero = True
                    else:
                        elapsed = 0
                        if self.pause_time:
                            elapsed = (self.pause_time - self.start_time).total_seconds()
                        remaining_secs = duration - elapsed
                        if remaining_secs < 0: remaining_secs = 0
                        end_time = now + timedelta(seconds=remaining_secs)
                    end_str = end_time.strftime("%H:%M:%S")
                else:
                    end_time = now + timedelta(seconds=duration)
                    end_str = end_time.strftime("%H:%M:%S")
                    remaining_secs = duration
            elif mode == TimerMode.FINISH_AT:
                end_str = self.current_timer_data['target_time'] + ":00"
                # Approx remaining
                target_dt = datetime.combine(now.date(), datetime.strptime(end_str, "%H:%M:%S").time())
                remaining_secs = (target_dt - now).total_seconds()
                if remaining_secs <= 0:
                    if not self.preview_display.settings.get('allow_overtime', False):
                        remaining_secs = 0
                    if not self.has_flashed_zero:
                        if (target_dt - now).total_seconds() > -2:
                            self.trigger_flash_output()
                        self.has_flashed_zero = True
                        if not self.preview_display.settings.get('allow_overtime', False) and self.preview_display.settings.get('auto_advance', False):
                            QTimer.singleShot(600, self.play_next)
        
        self.op_end_label.setText(end_str)

        if not self.current_timer_data:
            if not self.run_sheet_data:
                 self.preview_display.update_state("00:00", "Ready", 0)
                 self.projector.display.update_state("00:00", "Ready", 0)
            return
        
        self.update_display_text(remaining_secs)

    def update_display_text(self, remaining_secs=0):
        data = self.current_timer_data
        mode = data['mode']
        title = data['title']
        text = "00:00"
        progress = 0
        is_overtime = False
        
        if mode == TimerMode.TOD:
            text = QTime.currentTime().toString("HH:mm:ss")
            progress = 0
        elif mode == TimerMode.FINISH_AT:
            target_str = data['target_time']
            target = datetime.combine(datetime.now().date(), datetime.strptime(target_str, "%H:%M").time())
            now = datetime.now()
            diff = target - now
            total_seconds = diff.total_seconds()
            if total_seconds <= 0:
                is_overtime = True
                if not self.preview_display.settings.get('allow_overtime', False):
                    total_seconds = 0
                    prefix = ""
                else: 
                    total_seconds = abs(total_seconds)
                    prefix = "+"
            else: prefix = ""
            m, s = divmod(int(total_seconds), 60)
            h, m = divmod(m, 60)
            if h > 0: text = f"{prefix}{h}:{m:02d}:{s:02d}"
            else: text = f"{prefix}{m:02d}:{s:02d}"
            progress = 100 if is_overtime else 0
        elif mode in [TimerMode.COUNTDOWN, TimerMode.COUNTUP]:
            duration_secs = data['duration_mins'] * 60
            if self.start_time is None: elapsed = 0
            else:
                if self.is_running: elapsed = (datetime.now() - self.start_time).total_seconds()
                else:
                    if self.pause_time: elapsed = (self.pause_time - self.start_time).total_seconds()
                    else: elapsed = 0
            if mode == TimerMode.COUNTDOWN:
                remaining = duration_secs - elapsed
                if remaining <= 0:
                    is_overtime = True
                    if not self.preview_display.settings.get('allow_overtime', False):
                        remaining = 0
                        prefix = ""
                    else:
                        remaining = abs(remaining)
                        prefix = "+"
                else: prefix = ""
                m, s = divmod(int(remaining), 60)
                h, m = divmod(m, 60)
                if h > 0: text = f"{prefix}{h}:{m:02d}:{s:02d}"
                else: text = f"{prefix}{m:02d}:{s:02d}"
                progress = (elapsed / duration_secs) * 100 if duration_secs > 0 else 0
            else:
                m, s = divmod(int(elapsed), 60)
                h, m = divmod(m, 60)
                text = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                progress = (elapsed / duration_secs) * 100 if duration_secs > 0 else 0

        # Pass remaining_secs for smart colors
        self.preview_display.update_state(text, title, progress, is_overtime, remaining_secs)
        self.projector.display.update_state(text, title, progress, is_overtime, remaining_secs)
        
        self.cache_web_states()

    def cache_web_states(self):
        disp = self.preview_display
        w_state = {
            "text": disp.timer_label.text(),
            "header": disp.header_text,
            "color": getattr(disp, 'current_timer_color', "#ffffff"),
            "header_color": disp.settings.get("header_color", "#58a6ff"),
            "progress_color": disp.settings.get("progress_color", "#238636"),
            "message_color": disp.settings.get("message_color", "#f6e05e"),
            "font_weight": disp.settings.get("font_weight", "Bold"),
            "timer_alignment": disp.settings.get("timer_alignment", "Center"),
            "progress": getattr(disp, 'progress_value', 0),
            "message": disp.message_text,
            "message_visible": disp.is_message_visible,
            "blackout": disp.is_blackout,
            "flash": not disp.flash_overlay.isHidden(),
            "bg_color": disp.settings.get("bg_color", "#000000"),
            "show_logo": disp.settings.get("show_logo", True),
            "show_clock": disp.settings.get("show_clock", True),
            "clock_text": disp.clock_text
        }
        self.web_json_cache = json.dumps(w_state)
        
        o_state = {
            "realtime": QTime.currentTime().toString("HH:mm:ss"),
            "running": self.is_running,
            "blackout": disp.is_blackout,
            "prev": None,
            "curr": None,
            "next": None,
            "text": disp.timer_label.text(),
            "color": getattr(disp, 'current_timer_color', "#ffffff"),
            "progress": getattr(disp, 'progress_value', 0),
            "is_overtime": (getattr(disp, 'progress_value', 0) >= 100)
        }
        curr_data = self.current_timer_data
        if curr_data:
            o_state["curr"] = {"title": curr_data.get("title", ""), "mode": curr_data.get("mode", "")}
            try:
                idx = self.run_sheet_data.index(curr_data)
                if idx > 0: o_state["prev"] = self.run_sheet_data[idx-1].get("title", "")
                if idx < len(self.run_sheet_data) - 1: o_state["next"] = self.run_sheet_data[idx+1].get("title", "")
            except: pass
        self.op_json_cache = json.dumps(o_state)

    def save_data(self):
        try:
            with open(RUN_SHEET_FILE, 'w') as f: json.dump(self.run_sheet_data, f)
        except Exception as e: print(f"Error saving: {e}")

    def load_data(self):
        if os.path.exists(RUN_SHEET_FILE):
            try:
                with open(RUN_SHEET_FILE, 'r') as f:
                    data = json.load(f)
                    for row in data: self.add_timer_row(row)
            except: pass
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    saved_settings = json.load(f)
                    for k, v in saved_settings.items():
                        if k in self.preview_display.settings:
                            if k in ['show_logo', 'show_clock', 'show_progress', 'smart_colors']:
                                if isinstance(v, str): v = v.lower() in ('true', '1', 'yes', 'on')
                                elif isinstance(v, int): v = bool(v)
                            self.preview_display.settings[k] = v
                    s = self.preview_display.settings
                    self.chk_logo.setChecked(bool(s.get('show_logo', False)))
                    self.chk_clock.setChecked(bool(s.get('show_clock', False)))
                    self.chk_prog.setChecked(bool(s.get('show_progress', False)))
                    self.chk_smart.setChecked(bool(s.get('smart_colors', False)))
                    self.chk_overtime.setChecked(bool(s.get('allow_overtime', False)))
                    self.chk_advance.setChecked(bool(s.get('auto_advance', False)))
                    self.font_combo.setCurrentFont(QFont(s.get('font_family', 'Arial')))
                    if hasattr(self, 'weight_combo'): self.weight_combo.setCurrentText(s.get('font_weight', 'Bold'))
                    if hasattr(self, 'align_combo'): self.align_combo.setCurrentText(s.get('timer_alignment', 'Center'))
                    self.bg_mode_combo.setCurrentText(s.get('bg_mode', 'Cover'))
                    self.sync_design_to_projector()
            except: pass

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f: json.dump(self.preview_display.settings, f)
        except: pass

    def closeEvent(self, event):
        self.web_server.stop()
        self.web_server.wait()
        self.projector.close()
        super().closeEvent(event)

def get_resource_path(relative_path):
    import sys, os
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    
    # Set up basic logging to file
    import logging
    import traceback
    
    log_file = os.path.join(os.path.dirname(__file__), 'timer_errors.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info(f"Starting {APP_NAME}...")

    # Load stylesheet from file
    try:
        style_path = get_resource_path('styles.qss')
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        logging.error(f"Could not load stylesheet: {e}")
        
    app.setApplicationName(APP_NAME)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(26, 32, 44))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(palette)
    window = ControllerWindow()
    window.show()
    try:
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Unhandled Application Crash: {e}\n{traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
