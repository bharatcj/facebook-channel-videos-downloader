import os
import re
import requests
import time
import psutil
import json
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import shutil

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


def print_banner():
    print(
        f"{CYAN}{BOLD}┌─────────────────────────────────────────────────────────┐{RESET}"
    )
    print(
        f"{CYAN}{BOLD}│              🎬 FACEBOOK VIDEO DOWNLOADER 🎬            │{RESET}"
    )
    print(
        f"{CYAN}{BOLD}│                 Professional Edition v2.0               │{RESET}"
    )
    print(
        f"{CYAN}{BOLD}└─────────────────────────────────────────────────────────┘{RESET}"
    )
    print()


def print_section(title):
    print(f"\n{MAGENTA}{BOLD}🔹 {title}{RESET}")
    print(f"{MAGENTA}{'─' * 60}{RESET}")


def print_success(msg):
    print(f"\n{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"\n{RED}❌ {msg}{RESET}")


def print_warning(msg):
    print(f"\n{YELLOW}⚠️  {msg}{RESET}")


def print_info(msg):
    print(f"\n{BLUE}ℹ️  {msg}{RESET}")


def print_progress(iteration, total, prefix="", suffix="", length=50, fill="█"):
    if total <= 0:
        total = 1
    iteration = max(0, min(iteration, total))
    percent = ("{0:.1f}").format(100.0 * (iteration / float(total)))
    filled_length = int(round(length * iteration / float(total)))
    filled_length = max(0, min(filled_length, length))
    bar = fill * filled_length + "─" * (length - filled_length)
    line = f"{prefix} │{bar}│ {percent}% {suffix}"
    width = shutil.get_terminal_size((100, 20)).columns
    pad = max(0, width - len(line) - 1)
    print("\r" + line + " " * pad, end="\r")
    if iteration == total:
        print()


def setup_driver_with_profile():
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and any(
                name in proc.info["name"].lower() for name in ["chromedriver"]
            ):
                proc.kill()
        except:
            pass
    time.sleep(1)

    chrome_options = Options()
    profile_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    service = Service(ChromeDriverManager().install())
    service.creationflags = subprocess.CREATE_NO_WINDOW

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.profile_dir = profile_dir
    return driver


def login_to_facebook(driver):
    print_section("FACEBOOK LOGIN")
    driver.get("https://www.facebook.com")
    time.sleep(4)

    if "login" in driver.current_url or "Facebook – log in or sign up" in driver.title:
        print_info("Facebook login required")
        print("Please complete the following steps:")
        print("1. A browser window will open")
        print("2. Log in to your Facebook account")
        print("3. Return here and press Enter")
        input("\n🎯 Press Enter AFTER you have successfully logged in...")

    print_success("Facebook session ready")
    return True


def get_all_video_urls(driver, base_url):
    print_section("DISCOVERING VIDEOS")
    print_info("Loading videos page...")
    driver.get(base_url)
    time.sleep(6)

    video_urls = set()
    scroll_count = 0
    no_new_videos_count = 0
    previous_count = 0
    consecutive_same_count = 0

    while scroll_count < 100:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        page_source = driver.page_source

        patterns = [
            r'https://www\.facebook\.com/[^"]+/videos/\d+[^"]*',
            r"https://www\.facebook\.com/watch/\?v=\d+[^\" ]*",
            r"https://www\.facebook\.com/reel/\d+",
            r'https://www\.facebook\.com/[^"]+/reels/\d+',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            for url in matches:
                vid = None
                if "/videos/" in url:
                    m = re.search(r"/videos/(\d+)", url)
                    if m:
                        vid = m.group(1)
                elif "/reel/" in url:
                    m = re.search(r"/reel/(\d+)", url)
                    if m:
                        vid = m.group(1)
                elif "/watch/" in url and "v=" in url:
                    m = re.search(r"[?&]v=(\d+)", url)
                    if m:
                        vid = m.group(1)
                if vid:
                    clean_url = f"https://www.facebook.com/watch/?v={vid}"
                    video_urls.add(clean_url)

        scroll_count += 1
        current_count = len(video_urls)

        print_progress(
            min(scroll_count, 100),
            100,
            prefix="Scrolling Progress",
            suffix=f"Found {current_count} videos",
        )

        if current_count == previous_count:
            consecutive_same_count += 1
            if consecutive_same_count >= 3:
                break
        else:
            consecutive_same_count = 0

        previous_count = current_count

        if current_count >= 1000:
            break

    print(f"\n🎯 Scrolling completed: {len(video_urls)} unique videos discovered")
    return list(video_urls)


def download_file(link, file_name, folder_path):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.facebook.com/",
        "Accept": "video/webm,video/mp4,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.facebook.com",
        "Sec-Fetch-Dest": "video",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }
    try:
        resp = requests.get(link, headers=headers, timeout=60, stream=True)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"

        total_size = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(os.path.join(folder_path, file_name), "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        return True, "Success"
    except Exception as e:
        return False, f"Request error: {str(e)}"


def _deep_find_urls(obj):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_deep_find_urls(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_deep_find_urls(v))
    elif isinstance(obj, str):
        s = obj.replace("\\u0025", "%").replace("\\/", "/")
        if ("http" in s) and any(x in s for x in [".m3u8", ".mpd", ".mp4"]):
            out.append(s)
    return out


def _try_extract_from_graphql(driver):
    found = []
    logs = []
    try:
        logs = driver.get_log("performance")
    except:
        return []
    for entry in logs:
        try:
            msg = json.loads(entry["message"])["message"]
            method = msg.get("method", "")
            if method == "Network.responseReceived":
                params = msg.get("params", {})
                resp = params.get("response", {})
                url = resp.get("url", "")
                mime = resp.get("mimeType", "") or ""
                if (
                    "graphql" in url
                    or "api/graphql" in url
                    or "video_data" in url
                    or "reels" in url
                    or "streaming" in url
                    or "reel" in url
                    or "playback" in url
                    or mime == "application/json"
                ):
                    req_id = params.get("requestId")
                    if not req_id:
                        continue
                    try:
                        body_obj = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": req_id}
                        )
                    except:
                        continue
                    body_text = body_obj.get("body", "")
                    if not body_text:
                        continue
                    try:
                        data = json.loads(body_text)
                        urls = _deep_find_urls(data)
                        for u in urls:
                            found.append(u)
                    except:
                        urls = re.findall(
                            r'(https?://[^"\'\s]+?(?:m3u8|mpd|mp4)[^"\'\s]*)', body_text
                        )
                        for u in urls:
                            found.append(u)
        except:
            continue
    return list(dict.fromkeys(found))


def _maybe_mbasic_fallback(driver, video_id):
    try:
        url = f"https://mbasic.facebook.com/watch/?v={video_id}"
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
        cand = re.findall(r'href="([^"]+)"', html)
        for u in cand:
            u = u.replace("&amp;", "&")
            if "video_redirect" in u or "fbcdn" in u:
                if not u.startswith("http"):
                    u = "https://mbasic.facebook.com" + u
                if any(x in u for x in [".mp4", ".m3u8", ".mpd"]):
                    return u
        return None
    except:
        return None


def _looks_drm(s):
    s_lower = s.lower()
    return (
        ("widevine" in s_lower)
        or ("drm" in s_lower)
        or ("com.widevine.alpha" in s_lower)
    )


def _rand_str(n):
    import random, string

    return "".join(random.choices(string.ascii_letters + string.digits + "-_", k=n))


def _repo_fallback_download(page_url, out_path):
    try:
        cookies = {
            "sb": _rand_str(24),
            "fr": f"{_rand_str(20)}.{_rand_str(30)}.{_rand_str(22)}..AAA.0.0.{_rand_str(6)}.{_rand_str(40)}",
            "datr": _rand_str(24),
            "wd": f"1920x1080",
            "ps_l": "1",
            "ps_n": "1",
        }
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        html = requests.get(
            page_url, headers=headers, cookies=cookies, timeout=30
        ).text.replace("\\", "")
        media_url = None
        try:
            tail = re.findall(r'd_url":"https://video(.*?)"', html)[-1]
            media_url = "https://video" + tail
        except:
            pass
        if not media_url:
            for pat in [
                r'"browser_native_hd_url":"(https[^"]+)"',
                r'"browser_native_sd_url":"(https[^"]+)"',
                r'"playable_url_quality_hd":"(https[^"]+)"',
                r'"playable_url":"(https[^"]+)"',
            ]:
                m = re.search(pat, html)
                if m:
                    media_url = m.group(1)
                    break
        if not media_url:
            return False
        media_url = media_url.replace("\\/", "/").replace("&amp;", "&")
        if any(x in media_url for x in [".m3u8", ".mpd"]):
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            hdrs = (
                f"Cookie: {cookie_str}\r\n"
                f"User-Agent: {headers['user-agent']}\r\n"
                f"Referer: https://www.facebook.com/\r\n"
            )
            cmd = f'ffmpeg -hide_banner -loglevel error -headers "{hdrs}" -i "{media_url}" -movflags +faststart -c copy "{out_path}"'
            code = subprocess.call(
                cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if (
                code != 0
                or not os.path.exists(out_path)
                or os.path.getsize(out_path) == 0
            ):
                return False
            return True
        r = requests.get(
            media_url,
            headers={
                "user-agent": headers["user-agent"],
                "referer": "https://www.facebook.com/",
            },
            stream=True,
            timeout=60,
        )
        if r.status_code != 200:
            return False
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        if os.path.getsize(out_path) == 0:
            return False
        return True
    except:
        return False


def download_video_with_selenium(driver, link, folder_path, filename, failed_log_path):
    try:
        m = (
            re.search(r"[?&]v=(\d+)", link)
            or re.search(r"reel/(\d+)", link)
            or re.search(r"videos/(\d+)", link)
        )
        normalized_link = link
        if m:
            normalized_link = f"https://www.facebook.com/watch/?v={m.group(1)}"

        print()
        print(f"🌐 Opening video page: {normalized_link}")
        try:
            _ = driver.get_log("performance")
        except:
            pass
        driver.get(normalized_link)
        time.sleep(5)

        try:
            driver.execute_script("window.scrollTo(0, 200);")
            driver.execute_script(
                'var v=document.querySelector("video"); if(v){v.muted=true; v.click(); try{v.play()}catch(e){}}'
            )
        except:
            pass

        page_source = driver.page_source

        video_id_match = re.search(r"[?&]v=(\d+)", normalized_link) or re.search(
            r"reel/(\d+)", normalized_link
        )
        if not video_id_match:
            with open(failed_log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"URL: {normalized_link}\nError: Could not extract video ID from URL\n\n"
                )
            return False

        video_id = video_id_match.group(1)

        patterns = [
            r'"browser_native_hd_url":"([^"]+)"',
            r'"browser_native_sd_url":"([^"]+)"',
            r'hd_src":"([^"]+)"',
            r'sd_src":"([^"]+)"',
            r'hd_src:"([^"]+)"',
            r'sd_src:"([^"]+)"',
            r'video_url":"([^"]+)"',
            r'"playable_url":"([^"]+)"',
            r'"playable_url_quality_hd":"([^"]+)"',
        ]

        video_link = None
        audio_link = None

        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            for match in matches:
                if match and (
                    "mp4" in match.lower()
                    or "m3u8" in match.lower()
                    or "mpd" in match.lower()
                ):
                    clean_url = match.replace("\\u0025", "%").replace("\\", "")
                    if clean_url.startswith("http"):
                        if (
                            "quality_hd" in pattern
                            or "hd_src" in pattern
                            or "browser_native_hd" in pattern
                        ):
                            video_link = clean_url
                        else:
                            if not video_link:
                                video_link = clean_url

        if not video_link:
            t0 = time.time()
            found_urls = []
            while time.time() - t0 < 20:
                urls = _try_extract_from_graphql(driver)
                found_urls.extend(urls)
                if found_urls:
                    break
                time.sleep(1)
            found_urls = list(dict.fromkeys(found_urls))
            strong = [u for u in found_urls if any(x in u for x in [".m3u8", ".mpd"])]
            if not strong:
                strong = [u for u in found_urls if ".mp4" in u]
            if strong:
                video_link = strong[0]

        if not video_link:
            alt = _maybe_mbasic_fallback(driver, video_id)
            if alt:
                video_link = alt

        repo_used = False
        video_path = os.path.join(folder_path, "video_temp.mp4")

        if not video_link:
            ok = _repo_fallback_download(normalized_link, video_path)
            repo_used = ok
            if not ok:
                with open(failed_log_path, "a", encoding="utf-8") as f:
                    f.write(
                        f"URL: {normalized_link}\nError: No video stream found in page source\n\n"
                    )
                return False

        if video_link and _looks_drm(video_link) or _looks_drm(page_source):
            ok = _repo_fallback_download(normalized_link, video_path)
            repo_used = ok
            if not ok:
                with open(failed_log_path, "a", encoding="utf-8") as f:
                    f.write(f"URL: {normalized_link}\nError: DRM protected stream\n\n")
                return False

        if not repo_used:
            print("⬇️  Downloading video stream...")
            cookie_str = "; ".join(
                [f"{c['name']}={c['value']}" for c in driver.get_cookies()]
            )
            headers = (
                f"Cookie: {cookie_str}\r\n"
                f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
                f"Referer: https://www.facebook.com/\r\n"
                f"Origin: https://www.facebook.com\r\n"
                f"Accept-Language: en-US,en;q=0.9\r\n"
            )
            cmd = f'ffmpeg -hide_banner -loglevel error -headers "{headers}" -i "{video_link}" -movflags +faststart -c copy "{video_path}"'
            code = subprocess.call(
                cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if (
                code != 0
                or not os.path.exists(video_path)
                or os.path.getsize(video_path) == 0
            ):
                if ".mp4" in video_link:
                    ok, err = download_file(video_link, "video_temp.mp4", folder_path)
                    if not ok:
                        ok2 = _repo_fallback_download(normalized_link, video_path)
                        repo_used = ok2
                        if not ok2:
                            with open(failed_log_path, "a", encoding="utf-8") as f:
                                f.write(
                                    f"URL: {normalized_link}\nError: Failed to download stream with ffmpeg\n\n"
                                )
                            return False
                else:
                    ok2 = _repo_fallback_download(normalized_link, video_path)
                    repo_used = ok2
                    if not ok2:
                        with open(failed_log_path, "a", encoding="utf-8") as f:
                            f.write(
                                f"URL: {normalized_link}\nError: Failed to download stream with ffmpeg\n\n"
                            )
                        return False

        audio_path = os.path.join(folder_path, "audio_temp.mp4")
        final_path = os.path.join(folder_path, f"{filename}.mp4")

        if os.path.exists(audio_path):
            try:
                cmd = f'ffmpeg -hide_banner -loglevel error -i "{video_path}" -i "{audio_path}" -c copy "{final_path}"'
                subprocess.call(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if os.path.exists(final_path):
                    os.remove(video_path)
                    os.remove(audio_path)
                    print_success(f"Downloaded: {filename}.mp4")
                    return True
                else:
                    print_warning("Merge failed, saving video only")
            except Exception as e:
                print_warning(f"FFmpeg merge failed: {e}")

        if os.path.exists(video_path):
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
            except:
                pass
            os.rename(video_path, final_path)
            print_success(f"Downloaded: {filename}.mp4")
            return True

        return False

    except Exception as e:
        with open(failed_log_path, "a", encoding="utf-8") as f:
            f.write(f"URL: {link}\nError: Selenium extraction failed - {str(e)}\n\n")
        return False


def get_downloaded_videos(folder_path):
    downloaded = set()
    if folder_path.exists():
        for file in folder_path.iterdir():
            if file.is_file() and file.suffix == ".mp4":
                downloaded.add(file.stem)
    return downloaded


def process_facebook_page(driver, facebook_page_id):
    facebook_videos_url = f"https://www.facebook.com/{facebook_page_id}/videos/"

    script_dir = Path(__file__).parent
    video_folder = script_dir / f"fb_{facebook_page_id}_videos"
    video_folder.mkdir(exist_ok=True)

    failed_log_path = script_dir / f"failed_{facebook_page_id}.txt"

    print_section("CHECKING EXISTING DOWNLOADS")
    downloaded_videos = get_downloaded_videos(video_folder)
    print_info(f"Found {len(downloaded_videos)} previously downloaded videos")

    print_section("SCANNING FOR VIDEOS")
    video_urls = get_all_video_urls(driver, facebook_videos_url)

    if not video_urls:
        print_error("No videos found on this page")
        return 0, 0, 0

    print_section("DOWNLOADING VIDEOS")
    successful_downloads = 0
    skipped_downloads = 0
    failed_downloads = 0

    for i, video_url in enumerate(video_urls, 1):
        video_id_match = (
            re.search(r"reel/(\d+)", video_url)
            or re.search(r"v=(\d+)", video_url)
            or re.search(r"videos/(\d+)", video_url)
        )

        if video_id_match:
            filename = f"video_{video_id_match.group(1)}"
            if filename in downloaded_videos:
                skipped_downloads += 1
                print_progress(
                    i,
                    len(video_urls),
                    prefix="Download Progress",
                    suffix=f"Skipped: {filename}",
                )
                continue
        else:
            filename = f"video_{i}"

        print_progress(
            i,
            len(video_urls),
            prefix="Download Progress",
            suffix=f"Processing: {filename}",
        )

        if download_video_with_selenium(
            driver, video_url, video_folder, filename, failed_log_path
        ):
            successful_downloads += 1
        else:
            failed_downloads += 1

        if i % 15 == 0:
            time.sleep(5)
        else:
            time.sleep(2)

    print()
    print_section("DOWNLOAD SUMMARY")
    print_success(f"Successful: {successful_downloads}")
    print_info(f"Skipped (existing): {skipped_downloads}")
    print_warning(f"Failed: {failed_downloads}")
    print_info(f"Total processed: {len(video_urls)}")

    if failed_downloads > 0:
        print_warning(f"Failed downloads logged to: {failed_log_path}")

    return successful_downloads, skipped_downloads, failed_downloads


def main():
    print_banner()

    print("🚀 Initializing Facebook Video Downloader...")
    driver = setup_driver_with_profile()

    try:
        login_to_facebook(driver)

        while True:
            print_section("PAGE SELECTION")
            facebook_page_id = input("📝 Enter Facebook Page ID: ").strip()

            if not facebook_page_id:
                print_error("Page ID cannot be empty")
                continue

            print(f"\n🎯 Starting download for: {facebook_page_id}")
            successful, skipped, failed = process_facebook_page(
                driver, facebook_page_id
            )

            print_section("CONTINUE DOWNLOAD")
            continue_download = (
                input("\n🔄 Download videos from another page? (y/n): ").strip().lower()
            )
            if continue_download not in ["y", "yes", "1"]:
                print_success("🎉 Download session completed!")
                break

    except Exception as e:
        print_error(f"Unexpected error: {e}")
    finally:
        print_section("CLEANUP")
        print_info("Closing browser...")
        driver.close()
        driver.quit()
        if hasattr(driver, "profile_dir") and os.path.exists(driver.profile_dir):
            shutil.rmtree(driver.profile_dir, ignore_errors=True)
        print_success("Cleanup completed!")


if __name__ == "__main__":
    main()
