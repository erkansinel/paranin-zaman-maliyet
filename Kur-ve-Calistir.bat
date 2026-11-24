<# : Paranin Zaman Maliyeti - kurulum ve baslatma (Windows)
@echo off
REM  Bu dosya hem toplu is dosyasi hem PowerShell betigidir.
REM  Cift tikladiginizda logolu bir kurulum/baslatma penceresi acar:
REM  GitHub'daki son surumu indirir, gerekenleri kurar, programi baslatir.
REM  Ayrintilar: docs/06-kurulum-ve-yayin.md
setlocal
set "PZM_BAT=%~f0"
set "PZM_ARGS=%*"
REM  PowerShell 7 icinden cagrilinca modul yolu karismasin
set "PSModulePath="
if defined PZM_ARAYUZSUZ (powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ([IO.File]::ReadAllText($env:PZM_BAT,[Text.Encoding]::UTF8))" & exit /b)
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "iex ([IO.File]::ReadAllText($env:PZM_BAT,[Text.Encoding]::UTF8))" & exit /b
#>

# ===========================================================================
#  Paranın Zaman Maliyeti · Decisora Danışmanlık A.Ş.
#  Kurulum ve başlatma penceresi (Windows PowerShell 5.1 ve üstü, ek kurulum gerekmez)
#
#  Kurulum klasörü: %USERPROFILE%\ParaninZamanMaliyeti
#    kaynak\   GitHub'dan inen program kodu (her açılışta güncellenir)
#    python\   taşınabilir Python (yalnızca ilk açılışta iner)
#    veri\     VERİLERİNİZ (pzm.db) - güncellemelerde silinmez
#    kurulum.log
#
#  İsteğe bağlı ortam değişkenleri:
#    PZM_KLASOR        kurulum klasörü
#    PZM_DAL           indirilecek GitHub dalı (varsayılan: main)
#    PZM_GIT_KULLANMA  1 ise Git kurulu olsa bile zip ile indirir
#    PZM_ARAYUZSUZ     1 ise pencere açmaz, konsola yazar (otomatik test için)
# ===========================================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}

$Repo     = 'erkansinel/paranin-zaman-maliyet'
$PySurum  = '3.12.10'
$Dal      = if ($env:PZM_DAL) { $env:PZM_DAL } else { 'main' }
$Klasor   = if ($env:PZM_KLASOR) { $env:PZM_KLASOR } else { Join-Path $env:USERPROFILE 'ParaninZamanMaliyeti' }
$Kaynak   = Join-Path $Klasor 'kaynak'
$PyDir    = Join-Path $Klasor 'python'
$Py       = Join-Path $PyDir 'python.exe'
$Veri     = Join-Path $Klasor 'veri'
$Gecici   = Join-Path $Klasor 'gecici'
$Log      = Join-Path $Klasor 'kurulum.log'
$Durumf   = Join-Path $Klasor 'calisiyor.txt'
$Arayuzsuz = ($env:PZM_ARAYUZSUZ -eq '1')
$TarayiciAc = -not (" $env:PZM_ARGS " -match ' --no-browser ')
$Sirket   = 'Decisora Danışmanlık A.Ş.'
$Urun     = 'Paranın Zaman Maliyeti'

New-Item -ItemType Directory -Force -Path $Klasor, $Veri | Out-Null
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ====" | Out-File -FilePath $Log -Encoding utf8

function Gunluk([string]$s) { Add-Content -Path $Log -Value $s -Encoding utf8 }

# ---------------------------------------------------------------- Arayüz
$UI = $null
if (-not $Arayuzsuz) {
  Add-Type -AssemblyName System.Windows.Forms, System.Drawing
  [System.Windows.Forms.Application]::EnableVisualStyles()
  try { Add-Type -Namespace PZM -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();'; [PZM.Dpi]::SetProcessDPIAware() | Out-Null } catch {}

  $Lacivert = [Drawing.Color]::FromArgb(64, 79, 108)
  $Mint     = [Drawing.Color]::FromArgb(159, 220, 205)
  $Gri      = [Drawing.Color]::FromArgb(110, 118, 135)
  $Zemin    = [Drawing.Color]::FromArgb(236, 239, 244)

  $amblemB64 = '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'
  $amblem = [Drawing.Image]::FromStream((New-Object IO.MemoryStream (,[Convert]::FromBase64String($amblemB64))))

  $f = New-Object Windows.Forms.Form
  $f.Text = "$Urun · $Sirket"
  $f.ClientSize = New-Object Drawing.Size(560, 330)
  $f.StartPosition = 'CenterScreen'
  $f.FormBorderStyle = 'FixedSingle'
  $f.MaximizeBox = $false
  $f.BackColor = [Drawing.Color]::White
  $f.Font = New-Object Drawing.Font('Segoe UI', 9.5)
  $f.AutoScaleDimensions = New-Object Drawing.SizeF(96, 96)
  $f.AutoScaleMode = 'Dpi'
  try { $f.Icon = [Drawing.Icon]::FromHandle(([Drawing.Bitmap]$amblem).GetHicon()) } catch {}

  # Üst bant: logo + ürün adı + şirket adı
  $bant = New-Object Windows.Forms.Panel
  $bant.SetBounds(0, 0, 560, 112); $bant.BackColor = $Lacivert
  $logo = New-Object Windows.Forms.PictureBox
  $logo.SetBounds(28, 24, 64, 64); $logo.SizeMode = 'Zoom'; $logo.Image = $amblem; $logo.BackColor = $Lacivert
  $baslik = New-Object Windows.Forms.Label
  $baslik.SetBounds(108, 26, 430, 34); $baslik.Text = $Urun; $baslik.ForeColor = [Drawing.Color]::White
  $baslik.Font = New-Object Drawing.Font('Segoe UI Semibold', 17)
  $sirketL = New-Object Windows.Forms.Label
  $sirketL.SetBounds(110, 62, 430, 24); $sirketL.Text = $Sirket; $sirketL.ForeColor = $Mint
  $sirketL.Font = New-Object Drawing.Font('Segoe UI', 9.5, [Drawing.FontStyle]::Bold)
  $bant.Controls.AddRange(@($logo, $baslik, $sirketL))

  $durumL = New-Object Windows.Forms.Label
  $durumL.SetBounds(32, 138, 496, 26); $durumL.Font = New-Object Drawing.Font('Segoe UI Semibold', 12); $durumL.ForeColor = $Lacivert
  $detayL = New-Object Windows.Forms.Label
  $detayL.SetBounds(32, 166, 496, 20); $detayL.ForeColor = $Gri; $detayL.AutoEllipsis = $true

  # Marka renginde ilerleme çubuğu
  $iz = New-Object Windows.Forms.Panel
  $iz.SetBounds(32, 198, 496, 8); $iz.BackColor = $Zemin
  $dolgu = New-Object Windows.Forms.Panel
  $dolgu.SetBounds(0, 0, 0, 8); $dolgu.BackColor = $Mint
  $iz.Controls.Add($dolgu)
  $adimL = New-Object Windows.Forms.Label
  $adimL.SetBounds(32, 212, 496, 20); $adimL.ForeColor = $Gri; $adimL.Font = New-Object Drawing.Font('Segoe UI', 8.5)

  function Yeni-Dugme($metin, $x, $birincil) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $metin; $b.SetBounds($x, 262, 150, 40); $b.FlatStyle = 'Flat'; $b.Cursor = 'Hand'
    $b.Font = New-Object Drawing.Font('Segoe UI Semibold', 9.5)
    if ($birincil) { $b.BackColor = $Lacivert; $b.ForeColor = [Drawing.Color]::White; $b.FlatAppearance.BorderSize = 0 }
    else { $b.BackColor = [Drawing.Color]::White; $b.ForeColor = $Lacivert; $b.FlatAppearance.BorderColor = [Drawing.Color]::FromArgb(205, 211, 222) }
    $b.Visible = $false
    return $b
  }
  $btnAc    = Yeni-Dugme 'Programı aç' 32 $true
  $btnVeri  = Yeni-Dugme 'Veri klasörü' 205 $false
  $btnKapat = Yeni-Dugme 'Kapat' 378 $false
  $btnLog   = Yeni-Dugme 'Ayrıntıları göster' 205 $false

  $script:hazir = $false
  $f.Add_FormClosing({
    if (-not $script:hazir) {
      if ($script:AltSurec -and -not $script:AltSurec.HasExited) { & taskkill.exe /T /F /PID $script:AltSurec.Id 2>&1 | Out-Null }
      Sunucuyu-Durdur
      [Environment]::Exit(0)
    }
  })
  $f.Controls.AddRange(@($bant, $durumL, $detayL, $iz, $adimL, $btnAc, $btnVeri, $btnKapat, $btnLog))
  $UI = $f

  $script:belirsiz = $false; $script:kayma = 0
  $zam = New-Object Windows.Forms.Timer
  $zam.Interval = 30
  $zam.Add_Tick({
    if ($script:belirsiz) {
      $g = $iz.ClientSize.Width; $p = [int]($g * 0.28)
      $script:kayma = ($script:kayma + [int]($g / 60)) % ($g + $p)
      $dolgu.SetBounds($script:kayma - $p, 0, $p, $iz.ClientSize.Height)
    }
  })
  $zam.Start()
  $f.Show()
  [Windows.Forms.Application]::DoEvents()
}

function Pompala { if ($UI) { [Windows.Forms.Application]::DoEvents() } }

function Durum([string]$baslik, [string]$detay = '', [int]$adim = 0) {
  Gunluk "[$adim/4] $baslik $detay"
  if ($UI) {
    $durumL.Text = $baslik; $detayL.Text = $detay
    if ($adim -gt 0) { $adimL.Text = "Adım $adim / 4" } else { $adimL.Text = '' }
    Pompala
  } else {
    if ($adim -gt 0) { Write-Host " [$adim/4] $baslik $detay" } else { Write-Host " $baslik $detay" }
  }
}
function Detay([string]$s) { if ($UI) { $detayL.Text = $s; Pompala } }
function Ilerleme([double]$oran) {   # 0..1 ; negatif = belirsiz
  if (-not $UI) { return }
  if ($oran -lt 0) { $script:belirsiz = $true }
  else { $script:belirsiz = $false; $dolgu.SetBounds(0, 0, [int]($iz.ClientSize.Width * [Math]::Min(1, $oran)), $iz.ClientSize.Height) }
  Pompala
}
function Bekle([int]$ms) { $s = [Diagnostics.Stopwatch]::StartNew(); while ($s.ElapsedMilliseconds -lt $ms) { Pompala; Start-Sleep -Milliseconds 40 } }

# Komutu penceresiz çalıştırır, çıktısını günlüğe yazar, beklerken arayüzü canlı tutar
function Calistir([string]$exe, [string]$argumanlar, [switch]$SonSatir) {
  Gunluk "> $exe $argumanlar"
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = $env:ComSpec
  $psi.Arguments = "/d /c `"`"$exe`" $argumanlar >> `"$Log`" 2>&1`""
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $p = [Diagnostics.Process]::Start($psi)
  $script:AltSurec = $p
  while (-not $p.HasExited) {
    Pompala; Start-Sleep -Milliseconds 60
    if ($SonSatir -and $UI) {
      try {
        $son = Get-Content -Path $Log -Tail 1 -Encoding utf8 -ErrorAction SilentlyContinue
        if ($son) { $detayL.Text = ($son -replace '\s+', ' ').Trim() }
      } catch {}
    }
  }
  $p.WaitForExit()
  return $p.ExitCode
}

function Indir([string]$url, [string]$hedef, [string]$ad) {
  Gunluk "indir: $url"
  $wc = New-Object Net.WebClient
  $wc.Headers['User-Agent'] = 'PZM-Kurulum'
  $t = $wc.DownloadFileTaskAsync($url, $hedef)
  while (-not $t.IsCompleted) {
    Pompala; Start-Sleep -Milliseconds 80
    $toplam = 0
    try { $toplam = [long]$wc.ResponseHeaders['Content-Length'] } catch {}
    $boy = 0; if (Test-Path $hedef) { try { $boy = (Get-Item $hedef).Length } catch {} }
    if ($toplam -gt 0) { Ilerleme ($boy / $toplam); Detay ("{0}: {1:N1} / {2:N1} MB" -f $ad, ($boy/1MB), ($toplam/1MB)) }
    else { Ilerleme -1; if ($boy -gt 0) { Detay ("{0}: {1:N1} MB" -f $ad, ($boy/1MB)) } }
  }
  if ($t.IsFaulted) { throw $t.Exception.InnerException }
}

function Zip-Ac([string]$zip, [string]$hedef) {
  $kod = "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory('$zip','$hedef')"
  $rc = Calistir 'powershell.exe' "-NoProfile -ExecutionPolicy Bypass -Command `"$kod`""
  if ($rc -ne 0) { throw "Arşiv açılamadı: $zip" }
}

function Saglikli([string]$url) {
  try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "$url/api/saglik"; return ($r.StatusCode -eq 200) } catch { return $false }
}

$script:Sunucu = $null
function Sunucuyu-Durdur {
  if ($script:Sunucu -and -not $script:Sunucu.HasExited) {
    & taskkill.exe /T /F /PID $script:Sunucu.Id 2>&1 | Out-Null
  }
  Remove-Item -Force -ErrorAction SilentlyContinue $Durumf
}

function Hata-Goster([string]$mesaj) {
  Gunluk "HATA: $mesaj"
  if (-not $UI) { Write-Host " HATA: $mesaj"; exit 1 }
  $script:hazir = $true
  $script:belirsiz = $false
  $dolgu.BackColor = [Drawing.Color]::FromArgb(220, 90, 90); $dolgu.SetBounds(0, 0, $iz.ClientSize.Width, $iz.ClientSize.Height)
  $durumL.ForeColor = [Drawing.Color]::FromArgb(185, 50, 50)
  $durumL.Text = 'Bir sorun oluştu'
  $detayL.Text = $mesaj; $adimL.Text = "Günlük: $Log"
  $btnAc.Visible = $false; $btnVeri.Visible = $false
  $btnLog.Visible = $true; $btnKapat.Visible = $true
  $btnLog.Add_Click({ Start-Process notepad.exe $Log })
  $btnKapat.Add_Click({ $UI.Close() })
  $UI.Add_FormClosed({ [Windows.Forms.Application]::ExitThread() })
  [Windows.Forms.Application]::Run($UI)
  exit 1
}

# ---------------------------------------------------------------- Zaten çalışıyor mu?
if (Test-Path $Durumf) {
  $eskiUrl = (Get-Content $Durumf -ErrorAction SilentlyContinue | Select-Object -First 1)
  if ($eskiUrl -and (Saglikli $eskiUrl)) {
    if ($TarayiciAc) { Start-Process $eskiUrl }
    if ($UI) { Durum 'Program zaten çalışıyor' 'Tarayıcıda açıldı.'; Bekle 1500; $UI.Close() }
    exit 0
  }
}

try {
  # ------------------------------------------------------------ 1) Son sürüm
  Durum 'Son sürüm denetleniyor' "GitHub: $Repo ($Dal)" 1
  Ilerleme -1
  $gitVar = ($env:PZM_GIT_KULLANMA -ne '1') -and [bool](Get-Command git.exe -ErrorAction SilentlyContinue)
  $indi = $false
  try {
    if ($gitVar -and (Test-Path (Join-Path $Kaynak '.git'))) {
      if ((Calistir 'git.exe' "-C `"$Kaynak`" fetch --depth 1 origin `"$Dal`"" -SonSatir) -ne 0) { throw 'git fetch başarısız' }
      if ((Calistir 'git.exe' "-C `"$Kaynak`" reset --hard FETCH_HEAD") -ne 0) { throw 'git reset başarısız' }
      $indi = $true
    } elseif ($gitVar -and -not (Test-Path $Kaynak)) {
      if ((Calistir 'git.exe' "clone --depth 1 --branch `"$Dal`" `"https://github.com/$Repo.git`" `"$Kaynak`"" -SonSatir) -ne 0) { throw 'git clone başarısız' }
      $indi = $true
    } else {
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Gecici
      New-Item -ItemType Directory -Force -Path $Gecici | Out-Null
      $zip = Join-Path $Gecici 'kaynak.zip'
      Indir "https://github.com/$Repo/archive/refs/heads/$Dal.zip" $zip 'Program'
      Durum 'Son sürüm açılıyor' '' 1; Ilerleme -1
      Zip-Ac $zip (Join-Path $Gecici 'acilan')
      $acilan = Get-ChildItem -Directory (Join-Path $Gecici 'acilan') | Select-Object -First 1
      if (-not $acilan -or -not (Test-Path (Join-Path $acilan.FullName 'app\launcher.py'))) { throw 'İndirilen arşiv beklenen dosyaları içermiyor' }
      if (Test-Path $Kaynak) {
        try { Remove-Item -Recurse -Force $Kaynak } catch { throw 'Eski sürüm silinemedi; program açık olabilir. Tüm pencerelerini kapatıp tekrar deneyin.' }
      }
      Move-Item $acilan.FullName $Kaynak
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Gecici
      $indi = $true
    }
  } catch {
    Gunluk "indirme hatası: $_"
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Gecici
    if (-not (Test-Path (Join-Path $Kaynak 'app\launcher.py'))) { throw "Program GitHub'dan indirilemedi. İnternet bağlantınızı kontrol edin." }
  }
  if ($indi) { Durum 'Son sürüm alındı' '' 1 } else { Durum 'Son sürüm alınamadı, mevcut sürümle devam ediliyor' 'İnternet bağlantısı olmayabilir.' 1; Bekle 1500 }
  Ilerleme 1

  # Bu dosyanın güncel kopyası kurulum klasöründe dursun (kısayollar onu çalıştırır)
  $yerelBat = Join-Path $Klasor 'Kur-ve-Calistir.bat'
  $yeniBat = Join-Path $Kaynak 'Kur-ve-Calistir.bat'
  try {
    if (Test-Path $yeniBat) { Copy-Item -Force $yeniBat $yerelBat }
    elseif ($env:PZM_BAT -and ($env:PZM_BAT -ne $yerelBat)) { Copy-Item -Force $env:PZM_BAT $yerelBat }
  } catch { Gunluk "bat kopyalanamadı: $_" }

  # ------------------------------------------------------------ 2) Python
  if (Test-Path $Py) {
    Durum 'Python hazır' '' 2; Ilerleme 1
  } else {
    Durum 'Taşınabilir Python indiriliyor' 'Yalnızca ilk açılışta, yaklaşık 15 MB' 2
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Gecici
    New-Item -ItemType Directory -Force -Path $Gecici | Out-Null
    $pz = Join-Path $Gecici 'python.zip'
    Indir "https://api.nuget.org/v3-flatcontainer/python/$PySurum/python.$PySurum.nupkg" $pz "Python $PySurum"
    Durum 'Python hazırlanıyor' '' 2; Ilerleme -1
    Zip-Ac $pz (Join-Path $Gecici 'py')
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $PyDir
    Move-Item (Join-Path $Gecici 'py\tools') $PyDir
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Gecici
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Klasor 'paketler.txt')
    if (-not (Test-Path $Py)) { throw 'Python kurulamadı.' }
    Ilerleme 1
  }

  # ------------------------------------------------------------ 3) Paketler
  $req = Join-Path $Kaynak 'requirements.txt'
  $kayitli = Join-Path $Klasor 'paketler.txt'
  $guncel = (Test-Path $kayitli) -and ([IO.File]::ReadAllText($req) -eq [IO.File]::ReadAllText($kayitli))
  if ($guncel) {
    Durum 'Paketler güncel' '' 3; Ilerleme 1
  } else {
    Durum 'Gerekli bileşenler kuruluyor' 'Bu adım ilk açılışta birkaç dakika sürebilir' 3
    Ilerleme -1
    $rc = Calistir $Py "-m pip install --disable-pip-version-check --no-warn-script-location --progress-bar off -r `"$req`"" -SonSatir
    if ($rc -ne 0) { throw 'Gerekli bileşenler kurulamadı. İnternet bağlantınızı kontrol edin.' }
    Copy-Item -Force $req $kayitli
    Ilerleme 1
  }

  # ------------------------------------------------------------ 4) Başlat
  Durum 'Program başlatılıyor' '' 4; Ilerleme -1
  $env:PYTHONPATH = $Kaynak
  $env:PYTHONIOENCODING = 'utf-8'
  $sunucuLog = Join-Path $Klasor 'sunucu.log'
  Remove-Item -Force -ErrorAction SilentlyContinue $sunucuLog
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = $env:ComSpec
  $psi.Arguments = "/d /c `"`"$Py`" -u -X utf8 -m app.launcher --no-browser --veri `"$Veri`" > `"$sunucuLog`" 2>&1`""
  $psi.WorkingDirectory = $Kaynak
  $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
  $script:Sunucu = [Diagnostics.Process]::Start($psi)

  $url = $null
  $sure = [Diagnostics.Stopwatch]::StartNew()
  while (-not $url) {
    Bekle 250
    if (Test-Path $sunucuLog) {
      $m = [regex]::Match((Get-Content -Raw -Encoding utf8 $sunucuLog -ErrorAction SilentlyContinue), 'http://127\.0\.0\.1:\d+')
      if ($m.Success -and (Saglikli $m.Value)) { $url = $m.Value }
    }
    if ($script:Sunucu.HasExited) {
      Get-Content -Encoding utf8 $sunucuLog -ErrorAction SilentlyContinue | ForEach-Object { Gunluk $_ }
      throw 'Program başlatılamadı.'
    }
    if ($sure.Elapsed.TotalSeconds -gt 120) { throw 'Program 2 dakika içinde başlamadı.' }
  }
  Set-Content -Path $Durumf -Value $url -Encoding ascii
  Gunluk "calisiyor: $url"

  # Masaüstü ve Başlat menüsü kısayolu (ilk açılışta)
  if (-not $Arayuzsuz) {
    try {
      $wsh = New-Object -ComObject WScript.Shell
      $ikon = Join-Path $Kaynak 'app\static\brand\pzm.ico'
      $komut = "`$env:PZM_BAT='$yerelBat'; "
      if ($env:PZM_KLASOR) { $komut += "`$env:PZM_KLASOR='$Klasor'; " }
      $komut += "iex ([IO.File]::ReadAllText(`$env:PZM_BAT,[Text.Encoding]::UTF8))"
      $yerler = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
      foreach ($yer in $yerler) {
        if (-not $yer) { continue }
        $lnk = Join-Path $yer "$Urun.lnk"
        $k = $wsh.CreateShortcut($lnk)
        $k.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        $k.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$komut`""
        $k.WorkingDirectory = $Klasor
        $k.WindowStyle = 7
        $k.Description = "$Urun · $Sirket"
        if (Test-Path $ikon) { $k.IconLocation = "$ikon,0" }
        $k.Save()
      }
    } catch { Gunluk "kısayol oluşturulamadı: $_" }
  }
} catch {
  Sunucuyu-Durdur
  Hata-Goster ([string]$_.Exception.Message)
}

# ---------------------------------------------------------------- Çalışıyor
if ($TarayiciAc) { Start-Process $url }

if (-not $UI) {
  Write-Host " Program calisiyor: $url"
  $script:Sunucu.WaitForExit()
  Remove-Item -Force -ErrorAction SilentlyContinue $Durumf
  exit 0
}

$script:hazir = $true
$script:belirsiz = $false; $dolgu.SetBounds(0, 0, $iz.ClientSize.Width, $iz.ClientSize.Height)
$durumL.Text = 'Program çalışıyor'
$detayL.Text = "Tarayıcınızda açıldı: $url"
$adimL.Text = 'Bu pencereyi küçültebilirsiniz; kapattığınızda program da kapanır.'
$btnAc.Visible = $true; $btnVeri.Visible = $true; $btnKapat.Visible = $true
$btnAc.Add_Click({ Start-Process $url })
$btnVeri.Add_Click({ Start-Process explorer.exe $Veri })
$btnKapat.Add_Click({ $UI.Close() })

# Bildirim alanı simgesi: küçültünce oraya iner
$tepsi = New-Object Windows.Forms.NotifyIcon
$tepsi.Icon = $UI.Icon
$tepsi.Text = "$Urun - çalışıyor"
$menu = New-Object Windows.Forms.ContextMenuStrip
[void]$menu.Items.Add('Programı aç', $null, { Start-Process $url })
[void]$menu.Items.Add('Pencereyi göster', $null, { $UI.Show(); $UI.WindowState = 'Normal'; $UI.Activate() })
[void]$menu.Items.Add('-')
[void]$menu.Items.Add('Kapat', $null, { $UI.Close() })
$tepsi.ContextMenuStrip = $menu
$tepsi.Visible = $true
$tepsi.Add_DoubleClick({ $UI.Show(); $UI.WindowState = 'Normal'; $UI.Activate() })
$script:ipucu = $false
$UI.Add_Resize({
  if ($UI.WindowState -eq 'Minimized') {
    $UI.Hide()
    if (-not $script:ipucu) { $tepsi.ShowBalloonTip(3000, $Urun, 'Program arka planda çalışmaya devam ediyor.', 'Info'); $script:ipucu = $true }
  }
})
$UI.Add_FormClosing({
  param($s, $e)
  $c = [Windows.Forms.MessageBox]::Show($UI, "Program kapatılsın mı?`nAçık tarayıcı sekmeleri çalışmayı durdurur. Verileriniz kaydedilmiştir.", $Urun, 'YesNo', 'Question')
  if ($c -ne 'Yes') { $e.Cancel = $true; return }
  Sunucuyu-Durdur
  $tepsi.Visible = $false; $tepsi.Dispose()
})
$UI.Add_FormClosed({ [Windows.Forms.Application]::ExitThread() })

# Sunucu kendiliğinden kapanırsa pencere de bunu göstersin
$izle = New-Object Windows.Forms.Timer
$izle.Interval = 2000
$izle.Add_Tick({
  if ($script:Sunucu.HasExited) {
    $izle.Stop()
    $durumL.Text = 'Program durdu'; $durumL.ForeColor = [Drawing.Color]::FromArgb(185, 50, 50)
    $detayL.Text = "Ayrıntılar: $(Join-Path $Klasor 'sunucu.log')"
    $btnAc.Visible = $false
  }
})
$izle.Start()

[Windows.Forms.Application]::Run($UI)
exit 0
