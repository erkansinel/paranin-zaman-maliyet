# 6. Kurulum ve Yayına Alma

## 6.1 Windows: çift tıkla çalışan paket (önerilen)

Kurulum ve Python gerektirmez.

1. `ParaninZamanMaliyeti-Windows.zip` dosyasını indirin.
2. Zip'e sağ tıklayın → **Tümünü ayıkla** → bir klasöre çıkarın (ör. Belgeler).
   Zip'in içinden doğrudan çalıştırmayın.
3. Çıkan klasördeki **Baslat.bat** dosyasına çift tıklayın. Siyah bir pencere
   açılır ve birkaç saniye içinde tarayıcıda program açılır.
4. İlk açılışta yönetici hesabınızı oluşturun. Kapatmak için siyah pencereyi kapatın.

Windows "Bilgisayarınız korundu" uyarısı gösterirse **Ek bilgi → Yine de çalıştır**.
Bu, dosyanın dijital imzasız olmasından kaynaklanan standart bir uyarıdır.

* Veriler paket klasöründeki `veri\pzm.db` dosyasındadır. Yedek için bu dosyayı kopyalayın;
  yeni sürüme geçerken `veri` klasörünü yeni pakete taşıyın.
* Program yalnızca o bilgisayardan erişilebilir (`127.0.0.1`), ağa açılmaz.
  8000 portu doluysa bir sonraki boş port otomatik seçilir.
* Örnek verilerle denemek için **Ornek-Veri-Yukle.bat** (giriş: `demo` / `demo1234`).

Paketi yeniden üretmek için: `python scripts/build_windows_package.py`
(çıktı: `dist/ParaninZamanMaliyeti-Windows.zip`). GitHub'daki **Windows paketi**
iş akışı her değişiklikte paketi üretir, gerçek bir Windows makinesinde açıp
dener ve indirilebilir dosya olarak saklar.

## 6.2 Kendi bilgisayarında kaynak koddan çalıştırma

Gereken: Python 3.12 veya üstü.

```bash
git clone https://github.com/erkansinel/paranin-zaman-maliyet.git
cd paranin-zaman-maliyet
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# (İsteğe bağlı) örnek firma ve evraklarla doldur: kullanıcı demo / parola demo1234
python -m app.demo

uvicorn app.main:app --reload
# veya tarayıcıyı otomatik açan başlatıcı:
python -m app.launcher
```

Tarayıcıda **http://localhost:8000** adresini açın. Veriler `data/pzm.db`
dosyasında kalıcı olarak saklanır.

API belgesi: **http://localhost:8000/api/belgeler**

## 6.3 İnternette yayınlama (Render.com)

Repo, [Render](https://render.com) için hazır bir tanım dosyası (`render.yaml`)
içerir. Bu dosya bir web servisi ve bir PostgreSQL veritabanını birlikte kurar.

1. render.com'da GitHub hesabınızla oturum açın.
2. **New → Blueprint** seçin ve `paranin-zaman-maliyet` reposunu bağlayın.
3. Render, `PZM_KURULUM_ANAHTARI` değerini soracaktır. Kendinize ait, tahmin
   edilmesi zor bir anahtar yazın ve not edin.
4. **Apply** deyin. Birkaç dakika içinde `https://paranin-zaman-maliyeti-xxxx.onrender.com`
   gibi bir adres verilir.
5. Adresi açın, **İlk kurulum** ekranında kurulum anahtarı ile yönetici
   hesabınızı oluşturun. Ardından Ayarlar'dan firmaları ve firma kullanıcılarını ekleyin.

### Ücretsiz plan sınırları (önemli)

* Ücretsiz web servisi 15 dakika kullanılmazsa uyur; ilk açılış 30-60 saniye sürebilir.
* Ücretsiz PostgreSQL veritabanı Render tarafından **sınırlı bir süre sonra
  silinir** (yazım tarihinde 30 gün). Deneme için uygundur.
* Müşteri firmalarda gerçek kullanım için web servisi ve veritabanını Render
  panelinden ücretli plana yükseltin (yazım tarihinde web servisi aylık ~7 $,
  veritabanı aylık ~6 $'dan başlar). Güncel fiyatları Render sitesinden kontrol edin.

## 6.4 Başka bir sunucuda (Docker)

```bash
docker build -t pzm .
docker run -p 8000:8000 -v pzm-veri:/data pzm                       # SQLite, kalıcı birim
docker run -p 8000:8000 -e DATABASE_URL=postgresql://... pzm         # PostgreSQL
```

## 6.5 Ortam değişkenleri

| Değişken | Açıklama | Varsayılan |
|---|---|---|
| `DATABASE_URL` | PostgreSQL bağlantı adresi | Yoksa SQLite |
| `PZM_DATA_DIR` | SQLite dosyasının klasörü | `./data` |
| `PZM_KURULUM_ANAHTARI` | Tanımlıysa ilk yönetici hesabı bu anahtarla oluşturulabilir. İnternete açık kurulumlarda **mutlaka** tanımlayın. | Yok |
| `PORT` | Docker içinde dinlenecek port | 8000 |

## 6.6 Yedekleme

* SQLite: `data/pzm.db` dosyasını kopyalamak yeterlidir.
* PostgreSQL: `pg_dump` veya barındırma servisinin yedekleme özelliği.

## 6.7 Testleri çalıştırma

```bash
pip install -r requirements-dev.txt
pytest -q
```
