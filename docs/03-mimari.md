# 3. Sistem Mimarisi

## 3.1 Genel bakış

```
┌──────────────────────────── Tarayıcı ────────────────────────────┐
│  index.html + app.js (Alpine.js)  ·  styles.css  ·  Chart.js     │
│  Girdi toplar, sonuçları gösterir. Finansal hesap YAPMAZ.        │
└───────────────────────────────┬───────────────────────────────────┘
                                │ JSON (tutarlar metin olarak)
┌───────────────────────────────▼───────────────────────────────────┐
│  Web API — FastAPI (app/api/)                                      │
│   accounts.py   kurulum, giriş, firma ve kullanıcı yönetimi        │
│   calc.py       kayıtsız anlık hesaplar                            │
│   documents.py  portföy, özet, CSV aktarımı                        │
│  security.py    parola özeti, oturum, firma erişim kontrolü        │
└──────────────┬───────────────────────────────────┬────────────────┘
               │                                   │
┌──────────────▼──────────────┐      ┌─────────────▼───────────────┐
│ Finansal hesaplama modülü    │      │ Veri katmanı (SQLAlchemy)    │
│ app/finance/                 │      │ app/models.py, app/db.py     │
│  money.py    Decimal, kuruş  │      │ SQLite (yerel) veya          │
│  dates.py    gün, ay+gün     │      │ PostgreSQL (sunucu)          │
│  discount.py PV formülleri   │      └──────────────────────────────┘
│  analysis.py karşılaştırma,  │
│              peşin, portföy  │
│ Web/DB'den tamamen bağımsız. │
└──────────────────────────────┘
```

## 3.2 Tasarım ilkeleri

1. **Hesaplama modülü bağımsızdır.** `app/finance/` hiçbir web, veritabanı veya
   arayüz kütüphanesi içe aktarmaz. Aynı modül bir komut satırı aracında, bir
   Excel eklentisinde veya başka bir sistemde aynen kullanılabilir:

   ```python
   from datetime import date
   from app.finance import value_document, Method

   v = value_document("1000000", date(2026, 8, 29), "40",
                      Method.COMPOUND, valuation_date=date(2026, 1, 1))
   print(v.present_value)   # 801522.67
   ```

2. **Tek doğruluk kaynağı sunucudadır.** Tarayıcı hiçbir finansal formül
   çalıştırmaz; yalnızca sunucunun hesapladığı sonuçları biçimlendirir. Böylece
   ekran, rapor ve CSV aynı sayıyı gösterir.

3. **Hassasiyet katmanlar boyunca korunur.** Decimal → veritabanında metin →
   JSON'da metin → ekranda Türkçe biçim.

4. **Firma izolasyonu API katmanında zorunludur.** Her portföy uç noktası
   `accessible_company()` kontrolünden geçer; firma kullanıcısı başka firmanın
   verisine URL'yi değiştirerek de ulaşamaz (testlerle doğrulanmıştır).

## 3.3 Teknoloji seçimleri

| Katman | Teknoloji | Neden? |
|---|---|---|
| Dil | Python 3.12+ | Finansal hesaplar için güçlü `decimal` desteği, okunabilirlik, istek üzerine |
| Web çatısı | FastAPI | Modern, hızlı, otomatik API belgesi (`/api/belgeler`) |
| Veritabanı erişimi | SQLAlchemy 2 | SQLite ve PostgreSQL arasında kod değişmeden geçiş |
| Veritabanı | SQLite (yerel), PostgreSQL (sunucu) | Kurulumsuz başlangıç; sunucuda çok kullanıcılı güvenilir depolama |
| Arayüz | Alpine.js + Chart.js + özel CSS | Derleme adımı gerektirmez; hafif, hızlı, modern görünüm |
| Yazı tipi | Inter (uygulama içinde) | Rakamlar için tablo hizalı (tabular) yazım, Türkçe karakter desteği |

Tüm arayüz kütüphaneleri ve yazı tipi uygulamanın içinde gelir (`app/static/vendor`,
`app/static/fonts`); dış bir CDN'e bağımlılık yoktur. Kurumsal ağlarda ve
internet kısıtlı ortamlarda da çalışır.

## 3.4 Veri modeli

```
kullanici (id, username, full_name, password_hash, is_admin, active)
    │  çoktan çoğa
uyelik (kullanici_id, firma_id)
    │
firma (id, name, tax_no, default_rate, default_method, valuation_basis)
    │  1 → n
evrak (id, firma_id, doc_no, counterparty, doc_type[cek|senet], nominal,
       issue_date, maturity_date, annual_rate, method[bilesik|basit],
       status[portfoyde|tahsil_edildi|iade], bank, notes,
       pv_snapshot, cost_snapshot, snapshot_date, created_by, ...)

oturum (token_hash, user_id, expires_at)
```

* **(firma, tür, evrak no)** benzersizdir; aynı çek iki kez girilemez.
* `pv_snapshot` / `cost_snapshot`: evrak **kaydedildiği gün** hesaplanan
  bugünkü değer ve zaman maliyeti (iz kaydı). Ekranlar ise her açılışta
  değeri **güncel tarihe göre yeniden hesaplar**, çünkü bugünkü değer her gün
  değişir.
* Firma silinirse evrakları da silinir; kullanıcı silinirse evraklar kalır.

## 3.5 Güvenlik

* Parolalar PBKDF2-SHA256 (310.000 tekrar, rastgele tuz) ile özetlenerek saklanır.
* Oturum, `HttpOnly` ve `SameSite=Lax` çerez ile taşınır; HTTPS üzerinde
  `Secure` bayrağı otomatik eklenir. Sunucuda yalnızca belirtecin SHA-256
  özeti tutulur. Oturum süresi 14 gündür.
* İnternete açık kurulumlarda `PZM_KURULUM_ANAHTARI` tanımlanırsa ilk yönetici
  hesabını yalnızca bu anahtarı bilen oluşturabilir.
* Rol kontrolü: firma ve kullanıcı ekleme/silme yalnızca yöneticidedir.

## 3.6 Kurumsal kimlik

Uygulama **Decisora Danışmanlık A.Ş.** kimliğiyle yayınlanır. Şirketin özgün
logosundan üretilen dosyalar `app/static/brand/` klasöründedir: tam logo
(`decisora-logo.png`, giriş kartı ve rapor başlığı), amblem (`decisora-amblem*.png`,
yan menü), `favicon.png` ve Windows kısayol simgesi `pzm.ico`. Kurulum penceresi
(`Kur-ve-Calistir.bat`) da aynı amblemi ve şirket adını gösterir. Kurum adı
giriş ekranında, yan menüde, rapor başlığında, yazdırma / PDF çıktısında ve
CSV dosyasının ilk satırında yer alır (CSV için `app/api/documents.py`
içindeki `HAZIRLAYAN` sabiti). Tema renkleri logodan alınmıştır:
lacivert `#404f6c` ve mint `#9fdccd` (`app/static/styles.css` başındaki
`--brand-*` değişkenleri).

## 3.7 Klasör yapısı

```
app/
  finance/        Finansal hesaplama modülü (bağımsız)
  api/            Web API uç noktaları
  static/         Arayüz (HTML, JS, CSS, gömülü kütüphaneler)
  db.py           Veritabanı bağlantısı
  models.py       Tablolar
  security.py     Parola, oturum, yetki
  demo.py         Örnek veri yükleyici
  main.py         Uygulama giriş noktası
tests/
  test_finance.py Hesaplama modülü testleri (şartnamedeki 7 senaryo dahil)
  test_api.py     Uçtan uca API testleri (yetki, firma ayrımı, portföy)
docs/             Bu dokümantasyon
Dockerfile, render.yaml   Sunucuya kurulum
```

## 3.8 Genişletilebilirlik

Gelecekteki özelliklerin bu mimaride nereye oturacağı
[07-yol-haritasi.md](07-yol-haritasi.md) dosyasında açıklanmıştır.
