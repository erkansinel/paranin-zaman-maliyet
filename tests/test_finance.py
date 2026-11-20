"""Finansal hesaplama modülü testleri.

Her senaryoda sonuç iki bağımsız yolla kontrol edilir:
  1) Elle türetilmiş sabit beklenen değer (kuruş düzeyinde),
  2) Python ``math`` (float, exp/log) ile ayrı bir formül uygulaması.
Modül Decimal kullanır; ikinci kontrol tamamen farklı bir aritmetik yoldur.
"""

import math
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.finance import (
    Method,
    PortfolioItem,
    Status,
    ValidationError,
    add_months,
    analyze_cash_offer,
    compare_methods,
    compare_rates,
    format_tl,
    months_and_days,
    summarize_portfolio,
    value_document,
)

BUGUN = date(2026, 1, 1)


def vade(days: int) -> date:
    return BUGUN + timedelta(days=days)


def float_pv_compound(fv, r, d):
    return fv * math.exp(-math.log1p(r) * d / 365)


def float_pv_simple(fv, r, d):
    return fv / (1 + r * d / 365)


# --------------------------------------------------------------------------- #
# Şartname Test 1: 1.000.000 TL, 240 gün, %40
# --------------------------------------------------------------------------- #

def test_1_milyon_240_gun_yuzde_40():
    v = value_document("1000000", vade(240), "40", valuation_date=BUGUN)
    assert v.days == 240
    assert v.present_value == Decimal("801522.67")
    assert v.time_cost == Decimal("198477.33")
    assert v.loss_pct == Decimal("19.8477")
    assert v.effective_annual_pct == Decimal("40.0000")  # bileşikte efektif = nominal oran
    assert abs(float(v.present_value) - float_pv_compound(1e6, 0.40, 240)) < 0.005
    # Kalan süre: 1 Ocak + 240 gün = 29 Ağustos 2026 -> 7 ay 28 gün
    assert (v.months, v.rem_days) == (7, 28)
    assert v.status is Status.ACTIVE


# Şartname Test 2: aynı tutar ve vade, %30
def test_1_milyon_240_gun_yuzde_30():
    v = value_document("1000000", vade(240), "30", valuation_date=BUGUN)
    assert v.present_value == Decimal("841546.94")
    assert v.time_cost == Decimal("158453.06")
    assert abs(float(v.present_value) - float_pv_compound(1e6, 0.30, 240)) < 0.005


# Şartname Test 3: 100.000 TL, 30 gün, %50
def test_100_bin_30_gun_yuzde_50():
    v = value_document("100000", vade(30), "50", valuation_date=BUGUN)
    assert v.present_value == Decimal("96722.33")
    assert v.time_cost == Decimal("3277.67")
    assert abs(float(v.present_value) - float_pv_compound(1e5, 0.50, 30)) < 0.005
    s = value_document("100000", vade(30), "50", Method.SIMPLE, valuation_date=BUGUN)
    assert s.present_value == Decimal("96052.63")
    assert abs(float(s.present_value) - float_pv_simple(1e5, 0.50, 30)) < 0.005


# Şartname Test 4: vadesi geçmiş evrak
def test_vadesi_gecmis_evrak():
    v = value_document("50000", vade(-15), "40", valuation_date=BUGUN)
    assert v.days == -15
    assert v.status is Status.OVERDUE
    assert v.present_value == Decimal("50000.00")  # iskonto uygulanmaz
    assert v.time_cost == Decimal("0.00")
    assert v.effective_annual_pct is None


# Şartname Test 5: aynı gün vadeli evrak
def test_ayni_gun_vadeli_evrak():
    v = value_document("75000", BUGUN, "40", valuation_date=BUGUN)
    assert v.days == 0
    assert v.status is Status.DUE_TODAY
    assert v.present_value == Decimal("75000.00")
    assert v.time_cost == Decimal("0.00")
    assert (v.months, v.rem_days) == (0, 0)


# Şartname Test 6: çok sayıda çekin portföy toplamı
def test_cok_sayida_cek_portfoy_toplami():
    items = []
    beklenen_fv = Decimal(0)
    beklenen_pv_float = 0.0
    for i in range(1, 201):  # 200 evrak
        fv = Decimal(1000 * i) + Decimal("0.55")
        days = (i * 7) % 400 - 20  # vadesi geçmişler dahil
        rate = Decimal(20 + (i % 6) * 5)
        method = Method.COMPOUND if i % 3 else Method.SIMPLE
        items.append(PortfolioItem(fv, vade(days), rate, method, ref=i))
        beklenen_fv += fv
        f = float(fv)
        r = float(rate) / 100
        if days <= 0:
            beklenen_pv_float += f
        elif method is Method.COMPOUND:
            beklenen_pv_float += float_pv_compound(f, r, days)
        else:
            beklenen_pv_float += float_pv_simple(f, r, days)

    s = summarize_portfolio(items, BUGUN)
    assert s.count == 200
    assert s.total_nominal == beklenen_fv
    # satır yuvarlamaları nedeniyle en fazla 200 * 0,005 TL sapma olabilir
    assert abs(float(s.total_present_value) - beklenen_pv_float) <= 1.0
    assert s.total_time_cost == s.total_nominal - s.total_present_value
    # toplam = satırların toplamı (tablo ile birebir tutarlılık)
    assert s.total_present_value == sum(v.present_value for _, v in s.valuations)
    # dağılımlar toplamla tutarlı
    assert sum(b["adet"] for b in s.buckets) == 200
    assert sum(b["nominal"] for b in s.buckets) == s.total_nominal
    assert sum(m["nominal"] for m in s.monthly) == s.total_nominal
    assert sum(m["bugunku_deger"] for m in s.monthly) == s.total_present_value
    # ortalama vade: vadesi geçmişler 0 sayılır
    days = [max((i * 7) % 400 - 20, 0) for i in range(1, 201)]
    assert s.avg_days_simple == Decimal(str(round(sum(days) / 200, 1)))


def test_bos_portfoy():
    s = summarize_portfolio([], BUGUN)
    assert s.count == 0
    assert s.total_nominal == 0
    assert s.avg_days_simple is None


def test_portfoy_elle_kontrol():
    items = [
        PortfolioItem(Decimal("1000000"), vade(240), Decimal("40")),
        PortfolioItem(Decimal("100000"), vade(30), Decimal("50")),
        PortfolioItem(Decimal("50000"), vade(-15), Decimal("40")),
    ]
    s = summarize_portfolio(items, BUGUN)
    assert s.total_nominal == Decimal("1150000")
    assert s.total_present_value == Decimal("801522.67") + Decimal("96722.33") + Decimal("50000.00")
    # ağırlıklı ortalama vade = (240*1.000.000 + 30*100.000 + 0*50.000) / 1.150.000
    assert s.avg_days_weighted == Decimal("211.3")
    assert s.avg_days_simple == Decimal("90.0")
    kovalar = {b["anahtar"]: b["adet"] for b in s.buckets}
    assert kovalar == {"vadesi_gecmis": 1, "0-30": 1, "31-90": 0, "91-180": 0, "181-365": 1, "365+": 0}


# Şartname Test 7: basit ve bileşik iskonto karşılaştırması
def test_basit_bilesik_karsilastirma():
    c = compare_methods("1000000", vade(240), "40", valuation_date=BUGUN)
    assert c.compound.present_value == Decimal("801522.67")
    assert c.simple.present_value == Decimal("791757.05")
    assert abs(float(c.simple.present_value) - float_pv_simple(1e6, 0.40, 240)) < 0.005
    assert c.difference == Decimal("9765.62")
    # 1 yıldan kısa vadede basit iskonto daha düşük PV verir
    assert c.simple.present_value < c.compound.present_value


def test_tam_bir_yilda_yontemler_esit_bir_yildan_uzunda_ters():
    c = compare_methods("1000000", vade(365), "40", valuation_date=BUGUN)
    assert c.compound.present_value == c.simple.present_value == Decimal("714285.71")
    c2 = compare_methods("1000000", vade(730), "40", valuation_date=BUGUN)
    assert c2.simple.present_value > c2.compound.present_value


# --------------------------------------------------------------------------- #
# Oran karşılaştırması
# --------------------------------------------------------------------------- #

def test_oran_karsilastirmasi_varsayilan_oranlar():
    rows = compare_rates("1000000", vade(240), valuation_date=BUGUN)
    assert [r.annual_rate_pct for r in rows] == [Decimal(x) for x in (25, 30, 35, 40, 45, 50)]
    for r in rows:
        exp = float_pv_compound(1e6, float(r.annual_rate_pct) / 100, 240)
        assert abs(float(r.present_value) - exp) < 0.005
    pvs = [r.present_value for r in rows]
    assert pvs == sorted(pvs, reverse=True)  # oran arttıkça PV azalır


def test_oran_karsilastirmasi_tekrar_eden_oranlar_tekillesir():
    rows = compare_rates("1000", vade(10), ["40", "40.0", "10"], valuation_date=BUGUN)
    assert len(rows) == 2


# --------------------------------------------------------------------------- #
# Peşin / vadeli
# --------------------------------------------------------------------------- #

def test_pesin_avantajli():
    a = analyze_cash_offer("1000000", vade(240), "40", "820000", valuation_date=BUGUN)
    assert a.valuation.present_value == Decimal("801522.67")
    assert a.advantage == Decimal("18477.33")
    assert a.decision == "pesin"
    # ima edilen oran: (1e6/820000)^(365/240)-1
    exp = ((1e6 / 820000) ** (365 / 240) - 1) * 100
    assert abs(float(a.implied_rate_pct) - exp) < 0.01


def test_vadeli_avantajli():
    a = analyze_cash_offer("1000000", vade(240), "40", "750000", valuation_date=BUGUN)
    assert a.decision == "vadeli"
    assert a.advantage == Decimal("-51522.67")
    assert "801.522,67 TL" in a.explanation


def test_pesin_nominalden_buyuk_olamaz():
    with pytest.raises(ValidationError):
        analyze_cash_offer("1000", vade(10), "40", "1001", valuation_date=BUGUN)


# --------------------------------------------------------------------------- #
# Doğrulama
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("tutar", ["0", "-5", "abc", "1.001", "NaN", "Infinity"])
def test_gecersiz_tutar(tutar):
    with pytest.raises(ValidationError) as e:
        value_document(tutar, vade(10), "40", valuation_date=BUGUN)
    assert e.value.field == "nominal"


@pytest.mark.parametrize("oran", ["-1", "1001", "x", "NaN"])
def test_gecersiz_oran(oran):
    with pytest.raises(ValidationError) as e:
        value_document("1000", vade(10), oran, valuation_date=BUGUN)
    assert e.value.field == "yillik_oran"


def test_vade_duzenleme_tarihinden_once_olamaz():
    with pytest.raises(ValidationError) as e:
        value_document("1000", date(2026, 1, 1), "40", issue_date=date(2026, 2, 1), valuation_date=BUGUN)
    assert e.value.field == "vade_tarihi"


def test_float_kabul_edilmez():
    with pytest.raises(TypeError):
        value_document(1000.5, vade(10), "40", valuation_date=BUGUN)


def test_sifir_oran():
    v = value_document("1000", vade(100), "0", valuation_date=BUGUN)
    assert v.present_value == Decimal("1000.00")


# --------------------------------------------------------------------------- #
# Tarih yardımcıları
# --------------------------------------------------------------------------- #

def test_gercek_gun_sayisi_artik_yil():
    v = value_document("1000", date(2028, 3, 1), "40", valuation_date=date(2028, 2, 1))
    assert v.days == 29  # 2028 artık yıl


def test_ay_sonu_tasmasi():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert months_and_days(date(2026, 1, 31), date(2026, 3, 1)) == (1, 1)
    assert months_and_days(date(2026, 1, 15), date(2026, 9, 14)) == (7, 30)


def test_tl_bicimi():
    assert format_tl(Decimal("1234567.891")) == "1.234.567,89 TL"
    assert format_tl(Decimal("0.005")) == "0,01 TL"
    assert format_tl(Decimal("-1000")) == "-1.000,00 TL"
