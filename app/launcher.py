"""Masaüstü başlatıcı: sunucuyu yerel olarak başlatır ve tarayıcıyı açar.

Windows paketindeki ``Baslat.bat`` bu dosyayı çalıştırır. Başka sistemlerde:

    python -m app.launcher            # tarayıcıyı açar
    python -m app.launcher --no-browser --port 8765

Veriler varsayılan olarak paket klasöründeki ``veri`` klasöründe (SQLite) tutulur.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


def _free_port(preferred: int) -> int:
    for port in [preferred, *range(preferred + 1, preferred + 50)]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_and_open(url: str, open_browser: bool) -> None:
    for _ in range(120):
        try:
            with urllib.request.urlopen(url + "/api/saglik", timeout=1) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    print()
    print("  Paranın Zaman Maliyeti çalışıyor:  " + url)
    print("  Tarayıcı açılmazsa bu adresi kopyalayıp tarayıcınıza yapıştırın.")
    print("  Programı kapatmak için bu pencereyi kapatın.")
    print()
    if open_browser:
        webbrowser.open(url)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Paranın Zaman Maliyeti - yerel başlatıcı")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--veri", help="Veri klasörü (varsayılan: paket içindeki 'veri')")
    p.add_argument("--no-browser", action="store_true", help="Tarayıcıyı açma")
    a = p.parse_args(argv)

    root = Path(__file__).resolve().parent.parent  # uygulama klasörü
    package_dir = root.parent
    if a.veri:
        data_dir = Path(a.veri)
    elif (package_dir / "python").is_dir():  # Windows paketi: <paket>/veri
        data_dir = package_dir / "veri"
    else:  # kaynak koddan çalıştırma: <repo>/data
        data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PZM_DATA_DIR"] = str(data_dir)
    os.environ.pop("DATABASE_URL", None)  # masaüstü sürüm her zaman yerel SQLite kullanır

    port = _free_port(a.port)
    url = f"http://127.0.0.1:{port}"
    print("  Paranın Zaman Maliyeti başlatılıyor...")
    print("  Veri klasörü: " + str(data_dir))

    import uvicorn  # ortam değişkenleri ayarlandıktan sonra içe aktar

    from app.main import app

    threading.Thread(target=_wait_and_open, args=(url, not a.no_browser), daemon=True).start()
    # Yalnızca bu bilgisayardan erişilir (127.0.0.1); ağdaki başka cihazlar erişemez.
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    sys.exit(main())
