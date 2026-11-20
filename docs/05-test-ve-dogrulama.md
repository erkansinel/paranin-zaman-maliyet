# 5. Test ve Doğrulama

## 5.1 Test yaklaşımı

Her hesaplama **iki bağımsız yolla** doğrulanır:

1. **Elle türetilmiş beklenen değer:** Formül adım adım uygulanarak bulunan
   kuruş düzeyindeki sonuç testte sabit olarak yazılıdır.
2. **Ayrı bir aritmetik yol:** Aynı formül Python `math` kütüphanesiyle
   (kayan nokta, `exp`/`log1p`) yeniden hesaplanır ve programın Decimal
   sonucuyla en fazla ±0,005 TL farkla örtüşmesi beklenir.

Hesaplama modülü ile API ayrı ayrı test edilir. API testleri SQLite'ta
çalışır; PostgreSQL üzerinde de aynı testler çalıştırılarak geçtiği doğrulanmıştır.

```bash
pip install -r requirements-dev.txt
pytest -q
# 44 passed
```

## 5.2 Şartnamedeki 7 test senaryosu

Değerleme tarihi testlerde 01.01.2026 olarak sabitlenmiştir.

| # | Senaryo | Beklenen / Bulunan | Test |
|---|---|---|---|
| 1 | 1.000.000 TL, 240 gün, %40 | PV **801.522,67 TL**, zaman maliyeti **198.477,33 TL**, değer kaybı %19,85, kalan süre 7 ay 28 gün | `test_1_milyon_240_gun_yuzde_40` ✅ |
| 2 | Aynı tutar ve vade, %30 | PV **841.546,94 TL**, zaman maliyeti **158.453,06 TL** | `test_1_milyon_240_gun_yuzde_30` ✅ |
| 3 | 100.000 TL, 30 gün, %50 | Bileşik PV **96.722,33 TL** (maliyet 3.277,67); basit PV **96.052,63 TL** | `test_100_bin_30_gun_yuzde_50` ✅ |
| 4 | Vadesi bugünden önce | 15 gün geçmiş: durum "vadesi geçmiş", PV = nominal, maliyet 0 | `test_vadesi_gecmis_evrak` ✅ |
| 5 | Aynı gün vadeli | d = 0, durum "bugün", PV = nominal, 0 ay 0 gün | `test_ayni_gun_vadeli_evrak` ✅ |
| 6 | Çok sayıda çekin portföy hesabı | 200 evrak (vadesi geçmiş dahil, karışık oran ve yöntem): toplam nominal birebir, toplam PV bağımsız hesapla ±1 TL içinde (200 satır × en çok 0,005 TL yuvarlama), dağılım ve aylık toplamlar ana toplamla birebir | `test_cok_sayida_cek_portfoy_toplami` ✅ |
| 7 | Basit / bileşik karşılaştırması | 1.000.000 TL, 240 gün, %40: bileşik 801.522,67, basit 791.757,05, fark 9.765,62 TL; 365 günde ikisi eşit (714.285,71); 730 günde basit > bileşik | `test_basit_bilesik_karsilastirma`, `test_tam_bir_yilda_...` ✅ |

### Elle doğrulama: Test 1

```
ln(1,40)              = 0,3364722366
240 / 365             = 0,6575342466
çarpım                = 0,2212420186
e^0,2212420186        = 1,2476253…
1.000.000 / 1,2476253 = 801.522,673… → 801.522,67 TL
```

### Elle doğrulama: Test 3 (basit)

```
1 + 0,50 × 30/365 = 1,0410958904
100.000 / 1,0410958904 = 96.052,6316 → 96.052,63 TL
```

## 5.3 Ek testler

**Hesaplama modülü (31 test)**

* Oran karşılaştırması: %25-%50 her oranda bağımsız hesapla örtüşme; oran arttıkça PV'nin azalması; tekrarlanan oranların tekilleştirilmesi.
* Peşin / vadeli: peşin avantajlı, vadeli avantajlı, ima edilen oran (%35,23), nominalden büyük peşin teklifin reddi.
* Doğrulama: sıfır, negatif, sayısal olmayan, 2'den fazla ondalık, NaN/sonsuz tutar; negatif, %1000 üstü, sayısal olmayan oran; vadenin düzenleme tarihinden önce olması; float girdinin reddi; %0 oran.
* Tarih: artık yıl (Şubat 2028 = 29 gün), ay sonu taşması (31 Ocak + 1 ay).
* TL biçimi: `1.234.567,89 TL`.

**API (13 test)**

* Kurulum anahtarı: anahtarsız ve yanlış anahtarla kurulum reddi; ikinci kez kurulum yapılamaması.
* Oturum: oturumsuz erişimin engellenmesi, hatalı parola, çıkış.
* Tutarların JSON'da metin olarak (ör. `"801522.67"`) dönmesi.
* Teslim tarihine göre değerleme.
* Hatalı girdilerin 422 ve Türkçe mesajla, ilgili alan adıyla dönmesi.
* **Firma ayrımı:** Yalnızca Beta firmasına yetkili kullanıcının Alfa'nın
  portföyünü, evraklarını göremediği; firma ve kullanıcı oluşturamadığı.
* Aynı evrak numarasının ikinci kez kaydedilememesi.
* Senaryo oranıyla portföy değerleme, tahsil edilen evrakın portföy toplamından çıkması, CSV aktarımı.

## 5.4 Arayüz doğrulaması

Arayüz gerçek bir tarayıcıda (Chromium) örnek verilerle açılarak tüm ekranlar
gezilmiş ve görüntülenmiştir (bkz. `docs/ekranlar/`). Kontrol edilenler:

* Tüm sayfalarda JavaScript hatası olmaması.
* 1440 px masaüstü ve 390 px telefon genişliğinde hiçbir sayfada yatay taşma olmaması.
* Açık ve koyu temada okunabilirlik.

Arayüz için otomatik (sürekli çalışan) tarayıcı testi bu sürümde yoktur;
yol haritasında yer almaktadır.
