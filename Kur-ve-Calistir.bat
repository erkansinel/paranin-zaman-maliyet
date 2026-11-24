@echo off
REM ==========================================================================
REM  Paranin Zaman Maliyeti - GitHub'dan indir, kur ve calistir
REM
REM  Bu dosyayi tek basina herhangi bir klasore kaydedip cift tiklamaniz yeterli.
REM  Her calistirmada:
REM    1. GitHub'daki son surumu indirir (git varsa git ile, yoksa zip olarak)
REM    2. Ilk seferde tasinabilir Python'u indirir (bilgisayara kurulum yapmaz)
REM    3. Gerekli Python paketlerini kurar (yalnizca degistiklerinde)
REM    4. Programi baslatir ve tarayiciyi acar
REM
REM  Her sey %USERPROFILE%\ParaninZamanMaliyeti klasorune kurulur:
REM    python\   tasinabilir Python
REM    kaynak\   GitHub'dan inen program kodu (her guncellemede yenilenir)
REM    veri\     VERILERINIZ (pzm.db) - guncellemelerde silinmez
REM
REM  Ileri kullanim (istege bagli ortam degiskenleri):
REM    PZM_KLASOR=...        kurulum klasoru
REM    PZM_DAL=...           indirilecek GitHub dali (varsayilan: main)
REM    PZM_GIT_KULLANMA=1    git kurulu olsa bile zip ile indir
REM  Bu dosyaya verilen parametreler programa aktarilir (orn. --no-browser).
REM ==========================================================================
setlocal EnableExtensions
title Paranin Zaman Maliyeti
chcp 65001 >nul

set "REPO=erkansinel/paranin-zaman-maliyet"
set "PY_SURUM=3.12.10"
if not defined PZM_DAL set "PZM_DAL=main"
if not defined PZM_KLASOR set "PZM_KLASOR=%USERPROFILE%\ParaninZamanMaliyeti"

set "KLASOR=%PZM_KLASOR%"
set "PY=%KLASOR%\python\python.exe"
set "KAYNAK=%KLASOR%\kaynak"
set "VERI=%KLASOR%\veri"
set "GECICI=%KLASOR%\gecici"

echo.
echo  ============================================================
echo   Paranin Zaman Maliyeti
echo   Kurulum klasoru: %KLASOR%
echo  ============================================================
echo.

if not exist "%KLASOR%" mkdir "%KLASOR%"
if not exist "%VERI%" mkdir "%VERI%"

where powershell >nul 2>nul
if errorlevel 1 (
  echo  HATA: Windows PowerShell bulunamadi. Bu dosya Windows 10 veya 11 gerektirir.
  goto :hata
)

REM --------------------------------------------------------------------------
REM  1) Son surumu GitHub'dan indir
REM --------------------------------------------------------------------------
echo  [1/4] Son surum GitHub'dan indiriliyor...

set "GIT_VAR=0"
if not "%PZM_GIT_KULLANMA%"=="1" (
  where git >nul 2>nul && set "GIT_VAR=1"
)

if exist "%KAYNAK%\.git" if "%GIT_VAR%"=="1" goto :git_guncelle
if not exist "%KAYNAK%" if "%GIT_VAR%"=="1" goto :git_klonla
goto :zip_indir

:git_klonla
git clone --depth 1 --branch "%PZM_DAL%" "https://github.com/%REPO%.git" "%KAYNAK%"
if errorlevel 1 goto :indirme_basarisiz
goto :indirme_tamam

:git_guncelle
git -C "%KAYNAK%" fetch --depth 1 origin "%PZM_DAL%"
if errorlevel 1 goto :indirme_basarisiz
git -C "%KAYNAK%" reset --hard FETCH_HEAD >nul
if errorlevel 1 goto :indirme_basarisiz
goto :indirme_tamam

:zip_indir
if exist "%GECICI%" rmdir /s /q "%GECICI%"
mkdir "%GECICI%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
  "$z=Join-Path $env:GECICI 'kaynak.zip';" ^
  "Invoke-WebRequest -UseBasicParsing -Uri ('https://github.com/'+$env:REPO+'/archive/refs/heads/'+$env:PZM_DAL+'.zip') -OutFile $z;" ^
  "[IO.Compression.ZipFile]::ExtractToDirectory($z, (Join-Path $env:GECICI 'acilan'))"
if errorlevel 1 goto :indirme_basarisiz
set "ACILAN="
for /d %%D in ("%GECICI%\acilan\*") do set "ACILAN=%%D"
if not defined ACILAN goto :indirme_basarisiz
if not exist "%ACILAN%\app\launcher.py" goto :indirme_basarisiz
if exist "%KAYNAK%" rmdir /s /q "%KAYNAK%"
if exist "%KAYNAK%" (
  echo  HATA: Eski surum silinemedi. Program acik olabilir; tum pencerelerini kapatip tekrar deneyin.
  goto :hata
)
move "%ACILAN%" "%KAYNAK%" >nul
if errorlevel 1 goto :indirme_basarisiz
rmdir /s /q "%GECICI%"
goto :indirme_tamam

:indirme_basarisiz
if exist "%GECICI%" rmdir /s /q "%GECICI%"
if exist "%KAYNAK%\app\launcher.py" (
  echo.
  echo  UYARI: Son surum indirilemedi ^(internet baglantisi yok olabilir^).
  echo         Bilgisayardaki mevcut surumle devam ediliyor.
  echo.
  goto :indirme_tamam
)
echo  HATA: Program GitHub'dan indirilemedi. Internet baglantinizi kontrol edin.
goto :hata

:indirme_tamam

REM --------------------------------------------------------------------------
REM  2) Tasinabilir Python (yalnizca ilk calistirmada)
REM --------------------------------------------------------------------------
if exist "%PY%" (
  echo  [2/4] Python hazir.
  goto :python_tamam
)
echo  [2/4] Tasinabilir Python %PY_SURUM% indiriliyor ^(ilk seferde, yaklasik 15 MB^)...
if exist "%GECICI%" rmdir /s /q "%GECICI%"
mkdir "%GECICI%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
  "$z=Join-Path $env:GECICI 'python.zip';" ^
  "Invoke-WebRequest -UseBasicParsing -Uri ('https://api.nuget.org/v3-flatcontainer/python/'+$env:PY_SURUM+'/python.'+$env:PY_SURUM+'.nupkg') -OutFile $z;" ^
  "$a=Join-Path $env:GECICI 'py'; [IO.Compression.ZipFile]::ExtractToDirectory($z, $a);" ^
  "Move-Item (Join-Path $a 'tools') (Join-Path $env:KLASOR 'python')"
if errorlevel 1 (
  if exist "%GECICI%" rmdir /s /q "%GECICI%"
  echo  HATA: Python indirilemedi. Internet baglantinizi kontrol edin.
  goto :hata
)
rmdir /s /q "%GECICI%"
if not exist "%PY%" (
  echo  HATA: Python kurulamadi.
  goto :hata
)
if exist "%KLASOR%\paketler.txt" del "%KLASOR%\paketler.txt"

:python_tamam

REM --------------------------------------------------------------------------
REM  3) Paketler (requirements.txt degistiyse)
REM --------------------------------------------------------------------------
if exist "%KLASOR%\paketler.txt" (
  fc /b "%KAYNAK%\requirements.txt" "%KLASOR%\paketler.txt" >nul 2>nul
  if not errorlevel 1 (
    echo  [3/4] Paketler guncel.
    goto :paket_tamam
  )
)
echo  [3/4] Gerekli paketler kuruluyor ^(birkac dakika surebilir^)...
"%PY%" -m pip install --disable-pip-version-check --no-warn-script-location -q -r "%KAYNAK%\requirements.txt"
if errorlevel 1 (
  echo  HATA: Paketler kurulamadi.
  goto :hata
)
copy /y "%KAYNAK%\requirements.txt" "%KLASOR%\paketler.txt" >nul

:paket_tamam

REM --------------------------------------------------------------------------
REM  4) Baslat
REM --------------------------------------------------------------------------
echo  [4/4] Program baslatiliyor. Tarayici birazdan acilacak.
echo.
set "PYTHONPATH=%KAYNAK%"
set "PYTHONIOENCODING=utf-8"
cd /d "%KAYNAK%"
"%PY%" -X utf8 -m app.launcher --veri "%VERI%" %*
if errorlevel 1 goto :hata
exit /b 0

:hata
echo.
echo  Bir sorun olustu. Bu pencerenin ekran goruntusunu paylasin.
pause
exit /b 1
