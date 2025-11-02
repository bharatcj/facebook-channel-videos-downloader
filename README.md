# 🎬 Facebook Channel Videos Downloader

Download public Facebook **page/channel** videos at scale from your own logged-in session. Handles Reels, `/videos/`, and `watch/?v=` links. Skips files you already downloaded. Tries multiple extraction strategies and uses `ffmpeg` for HLS/DASH streams.

> **We don’t store or see your credentials.** A real Chrome window opens that *you* control. The script never asks for your password. Still suspicious? ✅ Audit the code yourself (or ask your favorite AI to roast it). 😄

---

## ✨ Features

- ✅ Uses your authenticated Chrome session (Selenium)  
- ✅ Auto-discovers videos from a page’s `/videos/` tab  
- ✅ Normalizes links to `https://www.facebook.com/watch/?v=<ID>`  
- ✅ Extracts playable URLs from page source, GraphQL responses, and `mbasic` fallback  
- ✅ Extra parser-style fallback for stubborn cases  
- ✅ Saves `.m3u8`/`.mpd` streams via `ffmpeg -c copy`  
- ✅ **Skips already downloaded** files automatically  
- ✅ Colorful CLI with a tidy progress bar and clear status lines

> Some videos are **DRM-protected** (e.g., Widevine). Those are intentionally **not** downloaded; you’ll get a clear message.

---

## 🧩 Requirements

- **Python 3.9+**
- **Google Chrome**
- **ffmpeg** in your PATH  
  - Windows builds: https://www.gyan.dev/ffmpeg/builds/
- Python packages (see `requirements.txt`)

---

## 🚀 Quickstart

```bash
pip install -r requirements.txt
python main.py
````

When prompted:

1. A Chrome window pops up.
2. Log in to Facebook as usual (2FA, checks, etc.).
3. Return to the terminal and press **Enter**.
4. Enter the **Page ID** (the part after `facebook.com/`, e.g. `NASA`).

Downloads are saved in `fb_<PAGE_ID>_videos/` with filenames like `video_<ID>.mp4`.

---

## 🛠 How it Works (Short Version)

1. Opens the page’s `/videos/` feed and scrolls to discover videos.
2. Normalizes each to `watch/?v=<ID>`.
3. Tries to extract playable URLs via:

   * Page source keys (`playable_url`, `browser_native_hd_url`, etc.)
   * GraphQL network responses (Chrome DevTools protocol)
   * `mbasic.facebook.com` redirect trick
   * A parser-style fallback
4. If a stream is HLS/DASH, `ffmpeg` saves it with stream copy.
5. If the final file already exists, it’s skipped.

---

## 🧯 Troubleshooting

* **“ffmpeg not found”** → Install it and add to PATH; restart your terminal.
* **Chrome/Selenium won’t start** → Update Chrome; delete the temp Selenium profile folder if needed.
* **Stuck on login** → Complete Facebook checks/2FA in the Chrome window, then press Enter.
* **Many “DRM protected stream” messages** → Those videos are not downloadable (by design).

---

## 🔐 Respect Rights & Terms

Download only content you own or have permission to download and comply with Facebook’s Terms of Service. **Do not attempt to bypass DRM.**

---

## 📁 Project Structure

```
.
├─ main.py
├─ requirements.txt
├─ README.md
├─ LICENSE
└─ .gitignore
```

---

## 📝 License

Released under the **MIT License**. See `LICENSE`.

---

## 💬 Contributing

PRs welcome! If you add a clean, reliable extraction trick (that’s not sketchy), I’ll happily review it.

---

## 🙌 Spread the Word

If you want to download videos from a Facebook **channel/page**, point folks to this repo and let them roll!