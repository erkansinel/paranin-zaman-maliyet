# 1. Amaç ve Kapsam

## 1.1 Neden bu program?

Türkiye'de ticari hayatın önemli bir kısmı vadeli çek ve senetle döner. Bir satış
bugün yapılır, bedeli ise 3, 6, 8 hatta 12 ay sonra tahsil edilir. Muhasebe
kayıtlarında bu alacak **nominal tutarıyla** görünür: 1.000.000 TL'lik çek,
defterde 1.000.000 TL'dir.

Oysa ekonomik gerçeklik farklıdır. Yüksek faiz ve enflasyon ortamında
8 ay sonra tahsil edilecek 1.000.000 TL, bugün elde bulunan 1.000.000 TL ile
aynı değerde değildir. Aradaki fark **paranın zaman maliyetidir**:

* Bu para bugün elde olsaydı bankada değerlendirilebilir, borç kapatılabilir
  veya tedarikçiye peşin ödeme iskontosu alınabilirdi.
* Para beklenirken işletme bu boşluğu çoğu zaman kredi veya çek kırdırma ile
  kapatır ve bunun bedelini öder.

Bu program tek bir temel soruya cevap verir:

> **Gelecekte tahsil edeceğim belirli bir tutar, bugünün parasıyla gerçekte kaç TL değerindedir?**

Örnek: Bugün alınan, 240 gün vadeli 1.000.000 TL'lik çek, yıllık %40 iskonto
oranıyla bugün yalnızca **801.522,67 TL** değerindedir. Satışın görünmeyen
maliyeti **198.477,33 TL**'dir; yani nominal tutarın yaklaşık **%19,85**'i.

## 1.2 Kimler için?

Program, finans danışmanının hizmet verdiği **birden çok firmada** kullanılmak
üzere tasarlanmıştır:

| Kullanıcı | Ne yapar? |
|---|---|
| **Yönetici (danışman)** | Tüm firmaları ve kullanıcıları yönetir, her firmanın portföyünü görür. |
| **Firma kullanıcısı** (finans müdürü, muhasebe) | Yalnızca kendisine atanan firmanın portföyünü görür ve yönetir. |

Her firmanın portföyü, varsayılan iskonto oranı (sermaye maliyeti), varsayılan
hesaplama yöntemi ve değerleme esası birbirinden ayrıdır.

## 1.3 Hangi kararları destekler?

1. **Fiyatlama:** Vadeli satışta fiyata ne kadar vade farkı eklenmeli?
   (Zaman maliyeti doğrudan bu farkı gösterir.)
2. **Tahsilat stratejisi:** Müşteri "8 ay vadeli çek yerine bugün 820.000 TL
   nakit vereyim" derse kabul edilmeli mi? (Peşin / vadeli karşılaştırma)
3. **Oran duyarlılığı:** Faiz %30'dan %45'e çıkarsa portföyün bugünkü değeri ne
   kadar düşer? (Oran karşılaştırması ve portföy senaryo oranı)
4. **Nakit planlama:** Hangi ay ne kadar tahsilat bekleniyor, bunun bugünkü
   karşılığı nedir? (Aylık tahsilat beklentisi)
5. **Risk takibi:** Vadesi geçmiş veya yaklaşan evraklar hangileri?
   (Vade dağılımı ve durum etiketleri)

## 1.4 Kapsam (bu sürümde olanlar)

* Tek evrak değerlemesi: bileşik ve basit iskonto, sonuçların yan yana karşılaştırılması.
* Değerleme tarihi seçimi: **bugün** (varsayılan), **teslim alma tarihi** veya **özel tarih**.
* Oran karşılaştırması: istenen sayıda oranla tablo ve grafik.
* Peşin / vadeli karar analizi: eşdeğer peşin tutar, avantaj, ima edilen oran ve Türkçe açıklama.
* Çoklu firma, çoklu kullanıcı, rol bazlı erişim.
* Portföy yönetimi: evrak ekleme, düzenleme, tahsil edildi / iade işaretleme, silme.
* Portföy özeti: toplam nominal, toplam bugünkü değer, toplam zaman maliyeti,
  ortalama vade (basit ve tutar ağırlıklı), vade dağılımı, aylık tahsilat beklentisi.
* Portföy senaryosu: tüm portföyü tek bir oranla yeniden değerleme.
* Raporlar: yazdırılabilir / PDF'e kaydedilebilir portföy raporu, Excel'de açılan CSV aktarımı.
* Açık ve koyu tema, masaüstü / tablet / telefon uyumlu arayüz.

Bu sürümde **olmayan** özellikler ve nasıl eklenecekleri
[07-yol-haritasi.md](07-yol-haritasi.md) dosyasında dürüstçe listelenmiştir.
