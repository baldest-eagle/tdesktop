# tdesktop — Setup Guide
## For People Who Don't Use the Terminal

### What Is This?

This is a custom version of tdesktop (Telegram Desktop) with extra features (multi-monitor support, snap grids, floating overlays, and more). The installer sets everything up for you — no command prompt or technical knowledge needed.

---

### What You Need

- Windows 10 or Windows 11 (64-bit)
- About 300 MB to 500 MB of free disk space (the installer package download is ~80 MB)
- An internet connection (for Telegram itself, not for install)

---

### How to Install

1. **Find the installer file** — It's called `tdesktop-Setup.exe` and lives in `out\Debug` (or `out\Release`).

2. **Double-click it** — Windows may ask "Do you want to allow this app to make changes?" — click **Yes**.

3. **Follow the wizard** — The installer will walk you through:
   - **Welcome screen** → Click *Next*
   - **License agreement** → Read the GPL license, choose *I accept the agreement*, then click *Next*
   - **Install location** → Defaults to `%LOCALAPPDATA%\tdesktop` (per-user, no admin required) → Click *Next*
   - **Start Menu folder** → Select shortcut group name (default `tdesktop` is fine) → Click *Next*
   - **Shortcuts** → Select whether to create desktop and Start Menu shortcuts, then click *Next*
   - **Ready to Install** → Review settings and click *Install*
   - **Progress bar** → Wait a moment (usually under 30 seconds)
   - **Finish** → Leave "Launch tdesktop" checked and click *Finish*

4. **Done!** — Telegram will open. Sign in with your phone number just like regular Telegram.

---

### First Launch

- Telegram may ask for your phone number and a verification code (sent via SMS or an existing Telegram session).
- All your chats, groups, and channels will appear — this works exactly like the official Telegram Desktop.
- The extra features (snap grid, multi-monitor, etc.) can be found in Settings once you're logged in.

---

### If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| "Windows protected your PC" (SmartScreen) | Click *More info* → *Run anyway*. This is normal for unsigned custom installers. |
| "Telegram is already running" error | Close any existing Telegram window (check the system tray near the clock) and try again. The installer will also attempt to close it automatically. |
| Installer won't start | Right-click the installer → *Run as administrator*. |
| Missing DLL / crashes on launch | Install the latest [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) and try again. |
| Antivirus flags the installer | This is a false positive — it's not malware. Add an exception for the installer and the install folder. |

---

### How to Uninstall

1. Open **Settings → Apps → Installed apps**
2. Search for "tdesktop"
3. Click the **⋯** menu → **Uninstall**
4. Confirm

Or: Go to the Start Menu → "tdesktop" group → "Uninstall tdesktop".

---

### Where Are My Files?

- **App installed at:** `%LOCALAPPDATA%\tdesktop\`
- **Your data/settings:** `%APPDATA%\Telegram Desktop\`
- **Crash logs (if needed):** `%LOCALAPPDATA%\tdesktop\DebugLogs\`

> `%LOCALAPPDATA%` is usually `C:\Users\YOURNAME\AppData\Local\`
> `%APPDATA%` is usually `C:\Users\YOURNAME\AppData\Roaming\`

---

### Getting Help

If Telegram crashes or something doesn't work:

1. Open the install folder (right-click the desktop shortcut → *Open file location*)
2. Look in the `DebugLogs` subfolder
3. Attach the most recent log files when asking for help
