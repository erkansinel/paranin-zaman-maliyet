# 7. Yol Haritası

Bu bölüm, bu sürümde **bulunmayan** özellikleri ve mimaride nereye
ekleneceklerini açıklar. Burada listelenenler henüz yapılmamıştır.

| Özellik | Durum | Nereye / nasıl eklenir? |
|---|---|---|
| Güncel banka ticari kredi faizleriyle hesaplama | Yok. Oran elle girilir. | `app/finance/` dışında bir "oran kaynağı" servisi (ör. TCMB EVDS'den ağırlıklı ortalama ticari kredi faizi). Firma ayarındaki varsayılan oran bu kaynaktan önerilebilir. Hesaplama modülü değişmez. |
| Banka çek iskonto (kırdırma) maliyeti | Yok | `analysis.py`'ye `bank_discount()` fonksiyonu: banka iskonto oranı, valör günü, BSMV, komisyon. Sonuç "bankaya kırdırırsam elime geçen" tutar. |
| Banka masraf ve komisyonları | Yok | Aynı fonksiyonda sabit tutar + oran olarak; evrak kaydına isteğe bağlı alanlar. |
| Çek kırdırma / erken tahsilat karşılaştırması | Kısmen: Peşin / vadeli karşılaştırma mevcut. | Peşin teklif yerine "banka kırdırma net tutarı" girilerek aynı karar mantığı kullanılabilir. |
| Dövizli çek ve senet | Yok, yalnızca TL. | Evrak tablosuna `para_birimi`, değerlemeye döviz faizi ve kur. Hesaplama formülü aynı; toplama öncesi TL'ye çevrim. |
| Enflasyona göre reel değer | Yok | `analysis.py`'ye reel değer: beklenen enflasyonla ayrıca indirgeme (Fisher). Sonuç ekranına "reel değer" satırı. |
| Excel'e aktarma | **Var (CSV)**. Gerçek .xlsx biçimi yok. | `openpyxl` ile biçimli .xlsx (başlıklar, sayı biçimleri, grafik). |
| Farklı şirketlerin portföylerini ayrı yönetme | **Var.** Firma bazlı portföy ve kullanıcı yetkisi. | Gerekirse firma grubu (holding) düzeyinde konsolide rapor eklenebilir. |
| Gecikme maliyeti (vadesi geçmiş evrak) | Yok. Vadesi geçen evrak nominal değerle gösterilir. | Gecikme günü × günlük sermaye maliyeti; ayrıca tahsilat riski karşılığı. |
| Excel / CSV'den toplu evrak içe aktarma | Yok | Portföy ekranına dosya yükleme; satır bazlı doğrulama raporu. |
| Kullanıcı işlem geçmişi (denetim izi) | Kısmen: evrakta oluşturan kullanıcı ve tarih tutuluyor. | Ayrı `islem_kaydi` tablosu. |
| Otomatik arayüz testleri | Yok (arayüz elle ve tarayıcıda doğrulandı). | Playwright ile uçtan uca senaryolar. |
| Parolamı unuttum (e-posta ile sıfırlama) | Yok. Yönetici parolayı sıfırlayabilir. | E-posta servisi entegrasyonu. |

## Mimari neden hazır?

* **Hesaplama modülü bağımsız** olduğu için yeni finansal fonksiyonlar
  (`bank_discount`, `real_value`, döviz) web ve veritabanı koduna dokunmadan
  eklenip test edilebilir.
* **Firma** kavramı baştan veri modelinde olduğu için çoklu şirket yönetimi
  sonradan eklenecek bir yama değil, temel yapıdır.
* **SQLAlchemy** sayesinde SQLite'tan PostgreSQL'e kod değişmeden geçilir
  (testler iki veritabanında da çalıştırılmıştır).
