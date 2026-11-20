"""Windows için taşınabilir paket üretir (kurulum gerektirmez).

Çıktı: dist/ParaninZamanMaliyeti-Windows.zip

    ParaninZamanMaliyeti/
      Baslat.bat                 <- çift tıkla
      Ornek-Veri-Yukle.bat       <- isteğe bağlı demo verisi
      OKUBENI.txt
      python/                    <- gömülü Python (NuGet "python" paketi, 64 bit)
      uygulama/app/              <- uygulama kodu
      veri/                      <- ilk çalıştırmada oluşur (SQLite veritabanı)

Linux, macOS veya Windows üzerinde çalıştırılabilir:
    python scripts/build_windows_package.py
"""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PY_VERSION = "3.12.10"
PY_TAG = "312"
ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
NAME = "ParaninZamanMaliyeti"
OUT = DIST / NAME
# Masaüstü sürüm SQLite kullanır; PostgreSQL sürücüsü gerekmez.
# pip, hedef platformun ortam işaretlerini değerlendirmediği için Windows bağımlılıkları açıkça eklenir.
WIN_REQUIREMENTS = ["fastapi==0.165.0", "uvicorn==0.54.0", "SQLAlchemy==2.1.9", "pydantic==2.13.5",
                    "colorama", "tzdata"]

BASLAT = r"""@echo off
chcp 65001 >nul
title Paranin Zaman Maliyeti
cd /d "%~dp0"
set "PYTHONPATH=%~dp0uygulama"
set "PYTHONIOENCODING=utf-8"
"%~dp0python\python.exe" -X utf8 -m app.launcher %*
if errorlevel 1 (
  echo.
  echo Program bir hata ile kapandi. Bu pencerenin ekran goruntusunu paylasin.
  pause
)
"""

DEMO = r"""@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0uygulama"
set "PYTHONIOENCODING=utf-8"
set "PZM_DATA_DIR=%~dp0veri"
"%~dp0python\python.exe" -X utf8 -m app.demo
pause
"""

OKUBENI = """PARANIN ZAMAN MALİYETİ - Windows paketi
=======================================

KURULUM GEREKMEZ.

1. Bu zip dosyasına sağ tıklayın > "Tümünü ayıkla" deyin ve bir klasöre çıkarın
   (ör. Belgeler). Zip içinden doğrudan çalıştırmayın.
2. Çıkan klasördeki "Baslat.bat" dosyasına çift tıklayın.
3. Siyah bir pencere açılır ve birkaç saniye içinde tarayıcınızda program açılır.
   İlk açılışta yönetici hesabınızı oluşturun.
4. Programı kapatmak için siyah pencereyi kapatın.

Windows "Bilgisayarınız korundu" uyarısı verirse: "Ek bilgi" > "Yine de çalıştır".

Örnek verilerle denemek isterseniz (isteğe bağlı):
  "Ornek-Veri-Yukle.bat" dosyasını çift tıklayın, sonra Baslat.bat ile açıp
  kullanıcı adı: demo   parola: demo1234   ile giriş yapın.

VERİLERİNİZ
  Tüm kayıtlar "veri" klasöründeki pzm.db dosyasında tutulur.
  Yedek almak için bu dosyayı kopyalamanız yeterlidir.
  Yeni bir sürüme geçerken "veri" klasörünü yeni pakete taşıyın.

Program yalnızca bu bilgisayardan erişilebilir (http://127.0.0.1:8000);
internete veya ağa açılmaz.

Ayrıntılı dokümantasyon: https://github.com/erkansinel/paranin-zaman-maliyet
"""


def download_python(target: Path) -> None:
    url = f"https://api.nuget.org/v3-flatcontainer/python/{PY_VERSION}/python.{PY_VERSION}.nupkg"
    print("Python indiriliyor:", url)
    data = urllib.request.urlopen(url, timeout=300).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for m in z.namelist():
            if m.startswith("tools/") and not m.endswith("/"):
                dest = target / m[len("tools/"):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(m))


def install_packages(site_packages: Path) -> None:
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--no-compile",
           "--target", str(site_packages), "--platform", "win_amd64",
           "--python-version", PY_TAG, "--implementation", "cp", "--only-binary=:all:",
           *WIN_REQUIREMENTS]
    print("Paketler kuruluyor...")
    subprocess.run(cmd, check=True)


def write_crlf(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    download_python(OUT / "python")
    # Gereksiz büyük parçaları çıkar (test paketi, IDLE, Tk)
    for junk in ["Lib/test", "Lib/idlelib", "Lib/tkinter", "Lib/turtledemo", "tcl"]:
        shutil.rmtree(OUT / "python" / junk, ignore_errors=True)
    install_packages(OUT / "python" / "Lib" / "site-packages")
    shutil.copytree(ROOT / "app", OUT / "uygulama" / "app",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "data"))
    write_crlf(OUT / "Baslat.bat", BASLAT)
    write_crlf(OUT / "Ornek-Veri-Yukle.bat", DEMO)
    write_crlf(OUT / "OKUBENI.txt", OKUBENI)

    zip_path = DIST / f"{NAME}-Windows.zip"
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                z.write(f, Path(NAME) / f.relative_to(OUT))
    print(f"Hazır: {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
