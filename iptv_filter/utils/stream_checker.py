import requests
import time
from typing import Dict, List, Callable
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class StreamChecker:
    @staticmethod
    def check_stream(url: str, timeout: int = 5) -> Dict[str, any]:
        start = time.time()
        try:
            # Deep check for HLS
            if url.endswith('.m3u8'):
                response = requests.get(url, timeout=timeout)
                elapsed = time.time() - start

                if response.status_code == 403:
                    return {"status": "Geo-blocked", "icon": "🌐", "time": elapsed, "code": 403}
                elif response.status_code < 400:
                    if '#EXTM3U' in response.text:
                        status = "Slow" if elapsed > 2.0 else "Working"
                        icon = "⚠️" if elapsed > 2.0 else "✅"
                        return {"status": status, "icon": icon, "time": elapsed, "code": response.status_code}
                    else:
                        return {"status": "Dead", "icon": "❌", "time": elapsed, "code": response.status_code}
                else:
                    return {"status": "Dead", "icon": "❌", "time": elapsed, "code": response.status_code}

            # Standard check for others
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 405:
                response = requests.get(url, timeout=timeout, stream=True)
                response.close()

            elapsed = time.time() - start

            if response.status_code == 403:
                return {"status": "Geo-blocked", "icon": "🌐", "time": elapsed, "code": 403}
            elif response.status_code < 400:
                status = "Slow" if elapsed > 2.0 else "Working"
                icon = "⚠️" if elapsed > 2.0 else "✅"
                return {"status": status, "icon": icon, "time": elapsed, "code": response.status_code}
            else:
                return {"status": "Dead", "icon": "❌", "time": elapsed, "code": response.status_code}

        except requests.RequestException:
            return {"status": "Dead", "icon": "❌", "time": time.time() - start, "code": 0}

    @staticmethod
    def check_channels(channels: List[any], progress_callback: Callable[[int, int], None], done_callback: Callable[[], None], max_workers: int = 50):
        def worker():
            total = len(channels)
            completed = 0

            def check_and_update(ch):
                if ch.streams:
                    url = ch.streams[0].get("url")
                    if url:
                        res = StreamChecker.check_stream(url)
                        ch.status_icon = res["icon"]
                        ch.status_text = res["status"]
                    else:
                        ch.status_icon = "❓"
                        ch.status_text = "Unknown"
                else:
                    ch.status_icon = "❌"
                    ch.status_text = "No Stream"

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(check_and_update, ch) for ch in channels]
                for future in as_completed(futures):
                    completed += 1
                    if progress_callback and completed % 10 == 0:
                        progress_callback(completed, total)

            if progress_callback:
                progress_callback(total, total)

            if done_callback:
                done_callback()

        threading.Thread(target=worker, daemon=True).start()
