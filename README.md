# David's Timer

This Timer is a professional, highly customizable broadcast and stage timer application built in Python and PyQt6. Designed for live events, conferences, and studio broadcast environments, it provides a feature-rich control interface for managing presentation timings alongside a clean, distraction-free output intended for stage displays, confidence monitors, or projectors.

## Key Features

### 🎛️ Timer & Run Sheet Management
* **Flexible Modes**: Supports standard Countdown, Count Up, Time of Day, and "Finish At" (target end time) modes.
* **Dynamic Run Sheets**: Build a complete schedule of event timers in advance. Easily drag-and-drop to reorder, add, or delete items on the fly.
* **Auto-Advance**: Seamlessly roll into the next queued timer the moment the current duration finishes.
* **Overtime Tracking**: Can flip into an "Overtime" mode counting up with bold visual indicators when a speaker goes over their allotted time.
* **Quick Nudges**: Instantly add or subtract 30 seconds or 1 minute from a live running timer directly from the main interface.

### 🎨 Clean & Customizable Output
* **WYSIWYG Live Preview**: The control preview accurately reflects your real-time design exactly as the speaker will see it, with no weird UI boxes or elements.
* **Custom Branding**: Fully skin the timer output by setting background images, custom logos with scaling, and importing your event's specific font weight and color palettes.
* **Traffic Light Styling**: Optional automated "smart colors" adjust the progress bar and timer text to caution (yellow) at <60 seconds, and alert (red) at 0:00 to naturally cue the speaker.
* **On-Screen Messaging**: Trigger fullscreen or bottom-third message overlays (e.g., "Wrap Up", "Q&A Time") straight to the monitor to silently pass notes to the talent. 
* **Attention Grabbers**: "Blackout" screen toggle or "Flash" screen effect to instantly grab attention without disrupting the timer.

### 📱 Remote Web Operator Panel
Included natively via a lightweight background web-server process, requiring no external dependencies:
* Host locally: Connect from any phone, tablet, or secondary laptop on the same local network by navigating to `http://<your-local-ip>:8080/operator` (or locally at `127.0.0.1:8080/operator`).
* Run the show dynamically: View the run sheet, manipulate timers, quickly punch in times with a touch-friendly numpad, and trigger critical actions completely wirelessly.

### 💾 Templates System
Save your complete configurations, loaded run sheets, custom colors, fonts, and styling as a standalone `.nte` (New Timer Elite) template file, allowing you to instantly load the application perfectly configured for recurring weekly events.

---

## Installation & Running from Source

Ensure you have Python 3.9+ installed on your system. 

1. **Install Requirements**:
   ```bash
   pip install PyQt6
   ```

2. **Run the Application**:
   ```bash
   python broadcast_timer.py
   ```

## Compiling to an Executable
You can easily build a standalone Windows executable (`.exe`) via `PyInstaller`, which will bundle PyQt6 and all assets into a single package. 

If you have PyInstaller installed globally or in your environment (`pip install pyinstaller`), use the included configuration spec file in the project root:
```bash
pyinstaller BroadcastTimer.spec --noconfirm
```
Your compiled application, ready to be copied and run on any Windows system, will be generated inside the `dist` directory.
