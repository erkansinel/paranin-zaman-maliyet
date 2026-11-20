# 2. Finansal Yöntem ve Formüller

Bu bölüm programın yaptığı her hesabı, formülüyle ve elle doğrulanabilir
örnekleriyle açıklar. Kodda karşılığı `app/finance/` klasöründedir.

## 2.1 Semboller

| Sembol | Anlamı |
|---|---|
| **FV** | Vadede tahsil edilecek nominal tutar (TL) |
| **PV** | Bugünkü değer (TL) |
| **r** | Yıllık iskonto oranı, ondalık (%40 → 0,40) |
| **d** | Değerleme tarihi ile vade tarihi arasındaki **gerçek** gün sayısı |
| **t** | Yıl cinsinden süre: t = d / 365 |

## 2.2 Gün sayısı

Gün sayısı takvim üzerinden gerçek gün olarak hesaplanır (artık yıllar dahil):

```
d = vade_tarihi − değerleme_tarihi
```

Örnek: 01.02.2028 → 01.03.2028 = **29 gün** (2028 artık yıldır).

Yıl uzunluğu, şartnamedeki formüle uygun olarak **365 gün** kabul edilir
(ACT/365 sabit). Türkiye'de bankacılıkta da yaygın uygulama budur.

### Değerleme tarihi

| Seçenek | Ne zaman kullanılır? |
|---|---|
| **Bugün** (varsayılan) | "Elimdeki çek şu an kaç TL ediyor?" sorusu. Portföy ekranı her zaman bugüne (veya seçilen rapor tarihine) göre değerler. |
| **Teslim alma tarihi** | "Bu çeki aldığım gün satışın gerçek bedeli neydi?" sorusu. Fiyatlama analizinde kullanılır. |
| **Özel tarih** | Geçmiş veya gelecek bir tarihe göre değerleme (ör. dönem sonu raporu). |

Firma ayarlarından her firma için yeni hesaplamada varsayılan esas seçilebilir.

### Kalan ay ve gün

Kalan süre tam takvim ayı + kalan gün olarak gösterilir. Ay sonu taşmalarında
ayın son günü esas alınır (31 Ocak + 1 ay = 28/29 Şubat).

Örnek: 01.01.2026 → 29.08.2026 = 240 gün = **7 ay 28 gün**.

## 2.3 Bileşik iskonto (varsayılan yöntem)

```
PV = FV / (1 + r) ^ (d / 365)
```

Bileşik iskonto, paranın ara dönemde de yeniden değerlendirilebileceğini
(faizin faizi) varsayar. Farklı vadeleri birbiriyle tutarlı biçimde
karşılaştırdığı için varsayılan yöntemdir.

**Örnek (şartname test 1):** FV = 1.000.000 TL, d = 240, r = %40

```
t          = 240 / 365                   = 0,657534…
(1,40)^t   = e^(t × ln 1,40) = e^(0,657534 × 0,336472) = e^0,221242 = 1,247625…
PV         = 1.000.000 / 1,247625…        = 801.522,67 TL
```

## 2.4 Basit iskonto

```
PV = FV / (1 + r × d / 365)
```

**Aynı örnekle:**

```
1 + 0,40 × 240/365 = 1 + 0,263014 = 1,263014
PV = 1.000.000 / 1,263014 = 791.757,05 TL
```

### İki yöntemin farkı

| Vade | Sonuç |
|---|---|
| 1 yıldan kısa | Basit iskonto **daha düşük** PV verir |
| Tam 1 yıl (365 gün) | İki yöntem **eşittir** (ör. %40'ta 714.285,71 TL) |
| 1 yıldan uzun | Basit iskonto **daha yüksek** PV verir |

Program her tek hesapta diğer yöntemin sonucunu ve farkı da gösterir.

## 2.5 Sonuç ekranındaki göstergeler

| # | Gösterge | Formül |
|---|---|---|
| 1 | Nominal değer | FV |
| 2 | Vadeye kalan gün | d |
| 3 | Kalan ay ve gün | Bkz. 2.2 |
| 4 | Yıllık iskonto oranı | r |
| 5 | Bugünkü ekonomik değer | PV (kuruşa yuvarlanmış) |
| 6 | Paranın zaman maliyeti | FV − PV |
| 7 | Nominale göre değer kaybı | (FV − PV) / FV × 100 |
| – | Vade boyunca maliyet | (FV / PV − 1) × 100 → bugünkü paranın vadeye kadar kaç % büyümesi gerektiği |
| 8 | Yıllık efektif eşdeğer | (FV / PV)^(365/d) − 1 |
| 8 | Aylık bileşik eşdeğer | (1 + yıllık efektif)^(1/12) − 1 |
| – | Aylık basit eşdeğer | r / 12 (bilgi amaçlı) |

Notlar:

* Bileşik yöntemde yıllık efektif eşdeğer tanım gereği r'ye eşittir
  (ör. %40,00). Basit yöntemde ise daha yüksektir; çünkü basit iskonto aynı
  nominal oranla daha fazla indirim yapar. Örnekte basit %40 ≈ efektif %42,63.
* "Değer kaybı" nominal tutar üzerinden, "vade boyunca maliyet" bugünkü değer
  üzerinden hesaplanır. İkisi farklı sorulara cevap verir:
  - Değer kaybı %19,85: *1.000.000 TL'lik çekin %19,85'i zamana gidiyor.*
  - Vade boyunca maliyet %24,76: *Bugünkü 801.522,67 TL'nin 240 günde %24,76 büyümesi gerekiyor.*

## 2.6 Vadesi gelmiş ve geçmiş evrak

* **d = 0 (aynı gün vadeli):** İskonto uygulanmaz, PV = FV, zaman maliyeti 0.
* **d < 0 (vadesi geçmiş):** İskonto uygulanmaz, PV = FV. Evrak "Vadesi geçmiş"
  olarak işaretlenir ve tahsil edilmesi gerektiği belirtilir.

Gerekçe: Vadesi gelen tutar bugün tahsil edilebilir durumdadır; geleceğe ait
bir bekleme yoktur. Gecikmenin maliyeti (gecikme faizi, tahsilat riski) bu
sürümün kapsamı dışındadır ve ayrıca belirtilir. Portföy ortalama vadesinde
bu evraklar **0 gün** olarak hesaba katılır.

## 2.7 Peşin / vadeli karşılaştırması

Soru: *"Bu çeki kabul etmek yerine bugün kaç TL nakit alsaydım aynı olurdu?"*

1. Vadeli tutar, kullanıcının **kendi yıllık sermaye maliyeti** ile bugüne
   indirgenir. Sonuç **eşdeğer peşin tutar**dır (= PV).
2. Teklif edilen peşin tutar (C) ile karşılaştırılır:
   * C > PV → **Peşin avantajlı**. Fark = C − PV.
   * C < PV → **Vadeli avantajlı**. Peşinin cazip olması için en az PV talep edilmelidir.
   * C = PV → İki seçenek eşdeğer.
3. **İma edilen oran:** Peşin teklif, karşı tarafa hangi yıllık iskonto
   oranına karşılık geliyor?
   * Bileşik: r* = (FV / C)^(365/d) − 1
   * Basit:  r* = (FV / C − 1) × 365 / d

   r* sermaye maliyetinden düşükse peşin teklif lehinizedir.

**Örnek:** 1.000.000 TL, 240 gün, sermaye maliyeti %40, peşin teklif 820.000 TL

```
Eşdeğer peşin tutar = 801.522,67 TL
Avantaj             = 820.000 − 801.522,67 = +18.477,33 TL → Peşin avantajlı
İma edilen oran     = (1.000.000 / 820.000)^(365/240) − 1 = %35,23  (< %40)
```

Peşin teklifin nominal tutardan büyük olması anlamsız olduğundan hata olarak
reddedilir.

## 2.8 Oran karşılaştırması

Aynı evrak, kullanıcının seçtiği her oran için ayrı ayrı değerlenir.
Şartnamedeki örnek (1.000.000 TL, 240 gün, bileşik):

| Oran | Bugünkü değer | Zaman maliyeti | Değer kaybı | Basit iskontoyla PV |
|---|---:|---:|---:|---:|
| %25 | 863.531,82 | 136.468,18 | %13,65 | 858.823,53 |
| %30 | 841.546,94 | 158.453,06 | %15,85 | 835.240,27 |
| %35 | 820.920,47 | 179.079,53 | %17,91 | 812.917,59 |
| %40 | 801.522,67 | 198.477,33 | %19,85 | 791.757,05 |
| %45 | 783.240,28 | 216.759,72 | %21,68 | 771.670,19 |
| %50 | 765.973,89 | 234.026,11 | %23,40 | 752.577,32 |

> Not: "8 ay" vade, takvimde bugünden 8 ay sonrasıdır ve ayların uzunluğuna
> göre 242-245 gün tutabilir. Yukarıdaki tablo şartnamedeki **240 gün** içindir.

## 2.9 Portföy hesapları

| Gösterge | Tanım |
|---|---|
| Toplam nominal alacak | Σ FV (yalnızca "Portföyde" durumundaki evraklar) |
| Toplam bugünkü değer | Σ PV (her evrak kendi oranı ve yöntemiyle) |
| Toplam zaman maliyeti | Toplam nominal − toplam bugünkü değer |
| Basit ortalama vade | Σ max(d, 0) / adet |
| Tutar ağırlıklı ortalama vade | Σ (max(d, 0) × FV) / Σ FV |
| Vade dağılımı | Vadesi geçmiş, 0-30, 31-90, 91-180, 181-365, 365+ gün |
| Aylık tahsilat beklentisi | Vade ayına göre gruplanmış nominal ve bugünkü değer |

Toplamlar, satırlarda gösterilen **kuruşa yuvarlanmış** değerlerin toplamıdır.
Böylece tablo satırları ile toplam satırı her zaman kuruşu kuruşuna tutar.

**Senaryo oranı:** Portföy ve rapor ekranında bir oran girilirse, tüm
evraklar kendi kayıtlı oranları yerine bu tek oranla yeniden değerlenir
("Faiz %50 olursa portföyüm ne eder?").

## 2.10 Sayısal hassasiyet

* Tüm hesaplar Python `decimal` modülüyle, **40 anlamlı basamak** hassasiyetle yapılır.
  Kayan noktalı sayı (float) hiçbir finansal hesapta kullanılmaz; modül float
  girdiyi bilerek reddeder.
* Yuvarlama yalnızca sonuçta, **kuruş (2 ondalık)** düzeyinde ve **yarım yukarı**
  kuralıyla yapılır. Yüzdeler 4 ondalıkla saklanır, ekranda 2 ondalıkla gösterilir.
* Tutarlar veritabanında metin olarak saklanır ve sunucudan tarayıcıya metin
  olarak gönderilir; böylece hiçbir katmanda kuruş kaybı olmaz.

## 2.11 Girdi doğrulama

| Durum | Davranış |
|---|---|
| Tutar sıfır veya negatif | "Tutar sıfırdan büyük olmalıdır." |
| Tutar 2'den fazla ondalık | "Tutar en fazla 2 ondalık basamak (kuruş) içerebilir." |
| Tutar 1 trilyon TL üzeri | Üst sınır hatası |
| Oran negatif | "Yıllık oran negatif olamaz." |
| Oran %1000 üzeri | Muhtemel yazım hatası olarak reddedilir |
| Geçersiz tarih (ör. 30 Şubat) | "Geçerli bir tarih giriniz." |
| Vade < düzenleme tarihi | "Vade tarihi, düzenleme/teslim alma tarihinden önce olamaz." |
| Sayısal olmayan değer | "… sayısal bir değer olmalıdır." |

Hatalar arayüzde ilgili alanın altında Türkçe olarak gösterilir.
