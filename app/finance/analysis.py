"""Karşılaştırmalı analizler: oran duyarlılığı, yöntem karşılaştırması,
peşin/vadeli karar analizi ve portföy özetleri."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, localcontext
from typing import Iterable, Optional, Sequence

from .dates import today_tr
from .discount import (
    Method,
    Status,
    Valuation,
    implied_annual_rate,
    validate_amount,
    validate_rate_pct,
    value_document,
)
from .errors import ValidationError
from .money import FIN_CONTEXT, YUZ, D, Number, round_money, round_pct

VARSAYILAN_ORANLAR = [Decimal(x) for x in (25, 30, 35, 40, 45, 50)]


# --------------------------------------------------------------------------- #
# Oran karşılaştırması
# --------------------------------------------------------------------------- #

def compare_rates(
    nominal: Number,
    maturity_date: date,
    rates_pct: Sequence[Number] = VARSAYILAN_ORANLAR,
    method: Method = Method.COMPOUND,
    valuation_date: Optional[date] = None,
) -> list[Valuation]:
    """Aynı evrakın farklı yıllık oranlardaki bugünkü değerleri."""
    if not rates_pct:
        raise ValidationError("oranlar", "En az bir oran giriniz.")
    if len(rates_pct) > 50:
        raise ValidationError("oranlar", "En fazla 50 oran karşılaştırılabilir.")
    seen = []
    for r in rates_pct:
        v = validate_rate_pct(r, "oranlar")
        if v not in seen:
            seen.append(v)
    seen.sort()
    return [
        value_document(nominal, maturity_date, r, method, valuation_date) for r in seen
    ]


# --------------------------------------------------------------------------- #
# Basit / bileşik karşılaştırması
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class MethodComparison:
    compound: Valuation
    simple: Valuation
    difference: Decimal  # bileşik PV - basit PV

    def as_dict(self) -> dict:
        return {
            "bilesik": self.compound.as_dict(),
            "basit": self.simple.as_dict(),
            "fark": self.difference,
        }


def compare_methods(
    nominal: Number,
    maturity_date: date,
    annual_rate_pct: Number,
    valuation_date: Optional[date] = None,
    issue_date: Optional[date] = None,
) -> MethodComparison:
    c = value_document(nominal, maturity_date, annual_rate_pct, Method.COMPOUND, valuation_date, issue_date)
    s = value_document(nominal, maturity_date, annual_rate_pct, Method.SIMPLE, valuation_date, issue_date)
    return MethodComparison(c, s, c.present_value - s.present_value)


# --------------------------------------------------------------------------- #
# Peşin / vadeli karşılaştırması
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class CashOfferAnalysis:
    valuation: Valuation  # vadeli tahsilatın sermaye maliyetiyle bugünkü değeri
    cash_offer: Decimal
    advantage: Decimal  # peşin - PV ; >0 ise peşin avantajlı
    advantage_pct: Decimal  # avantajın PV'ye oranı (%)
    implied_rate_pct: Optional[Decimal]  # peşin teklifin ima ettiği yıllık iskonto oranı
    decision: str  # "pesin" | "vadeli" | "esit"
    explanation: str

    def as_dict(self) -> dict:
        return {
            "degerleme": self.valuation.as_dict(),
            "pesin_teklif": self.cash_offer,
            "esdeger_pesin_tutar": self.valuation.present_value,
            "avantaj": self.advantage,
            "avantaj_yuzde": self.advantage_pct,
            "ima_edilen_oran": self.implied_rate_pct,
            "karar": self.decision,
            "aciklama": self.explanation,
        }


def analyze_cash_offer(
    nominal: Number,
    maturity_date: date,
    cost_of_capital_pct: Number,
    cash_offer: Number,
    method: Method = Method.COMPOUND,
    valuation_date: Optional[date] = None,
) -> CashOfferAnalysis:
    """"Bu çek yerine bugün kaç TL nakit alsaydım aynı olurdu?" sorusunun cevabı.

    Vadeli tutar, kullanıcının kendi yıllık sermaye maliyetiyle bugüne
    indirgenir. Bu tutar "eşdeğer peşin tutar"dır. Teklif edilen peşin tutar
    bundan büyükse peşin, küçükse vadeli seçenek ekonomik olarak avantajlıdır.
    """
    offer = validate_amount(cash_offer, "pesin_teklif")
    val = value_document(nominal, maturity_date, cost_of_capital_pct, method, valuation_date)
    if offer > val.nominal:
        raise ValidationError(
            "pesin_teklif",
            "Peşin teklif, vadeli nominal tutardan büyük olamaz; böyle bir teklifte karar açıktır.",
        )
    adv = offer - val.present_value
    with localcontext(FIN_CONTEXT):
        adv_pct = adv / val.present_value * YUZ
    implied = implied_annual_rate(val.nominal, offer, val.days, method)
    implied_pct = round_pct(implied * YUZ, 2) if implied is not None else None

    from .money import format_pct, format_tl

    pv_s = format_tl(val.present_value)
    if val.days <= 0:
        decision = "esit" if adv == 0 else ("vadeli" if adv < 0 else "pesin")
        explanation = (
            "Evrakın vadesi gelmiş veya geçmiş; nominal tutar bugün tahsil edilebilir "
            f"durumda olduğundan eşdeğer peşin tutar {pv_s}'dir. "
            + ("Daha düşük bir peşin teklifin kabulü ekonomik değildir." if adv < 0 else "")
        ).strip()
    elif adv > 0:
        decision = "pesin"
        explanation = (
            f"Yıllık {format_pct(val.annual_rate_pct)} sermaye maliyetinizle vadeli tahsilatın bugünkü değeri "
            f"{pv_s}. Teklif edilen peşin tutar bundan {format_tl(adv)} daha yüksek; "
            f"peşin ödemeyi kabul etmek ekonomik olarak avantajlıdır. "
            f"Teklif, karşı tarafa yıllık yaklaşık {format_pct(implied_pct)} iskonto oranına karşılık geliyor; "
            f"bu oran sizin sermaye maliyetinizden düşük."
        )
    elif adv < 0:
        decision = "vadeli"
        explanation = (
            f"Yıllık {format_pct(val.annual_rate_pct)} sermaye maliyetinizle vadeli tahsilatın bugünkü değeri "
            f"{pv_s}. Teklif edilen peşin tutar bundan {format_tl(-adv)} daha düşük; "
            f"vadeyi beklemek ekonomik olarak daha avantajlıdır. "
            f"Peşin teklif yıllık yaklaşık {format_pct(implied_pct)} iskontoya karşılık geliyor; "
            f"bu oran sizin sermaye maliyetinizden yüksek. "
            f"Peşinin cazip olması için en az {pv_s} talep edilmelidir."
        )
    else:
        decision = "esit"
        explanation = (
            f"Teklif edilen peşin tutar, vadeli tahsilatın bugünkü değerine ({pv_s}) eşit; "
            "iki seçenek ekonomik olarak aynıdır."
        )
    return CashOfferAnalysis(val, offer, adv, round_pct(adv_pct, 2), implied_pct, decision, explanation)


# --------------------------------------------------------------------------- #
# Portföy özeti
# --------------------------------------------------------------------------- #

@dataclass
class PortfolioItem:
    """Portföy hesabı için gereken asgari evrak bilgisi."""

    nominal: Decimal
    maturity_date: date
    annual_rate_pct: Decimal
    method: Method = Method.COMPOUND
    ref: object = None  # çağıranın kimliği (ör. veritabanı id'si)


VADE_ARALIKLARI = [
    ("vadesi_gecmis", "Vadesi geçmiş", None, -1),
    ("0-30", "0-30 gün", 0, 30),
    ("31-90", "31-90 gün", 31, 90),
    ("91-180", "91-180 gün", 91, 180),
    ("181-365", "181-365 gün", 181, 365),
    ("365+", "365 günden uzun", 366, None),
]

AY_ADLARI = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


@dataclass
class PortfolioSummary:
    valuation_date: date
    count: int
    total_nominal: Decimal
    total_present_value: Decimal
    total_time_cost: Decimal
    loss_pct: Decimal
    avg_days_simple: Optional[Decimal]  # basit ortalama vade (gün)
    avg_days_weighted: Optional[Decimal]  # tutar ağırlıklı ortalama vade (gün)
    buckets: list = field(default_factory=list)
    monthly: list = field(default_factory=list)
    valuations: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "degerleme_tarihi": self.valuation_date,
            "adet": self.count,
            "toplam_nominal": self.total_nominal,
            "toplam_bugunku_deger": self.total_present_value,
            "toplam_zaman_maliyeti": self.total_time_cost,
            "deger_kaybi_yuzde": self.loss_pct,
            "ortalama_vade_gun": self.avg_days_simple,
            "agirlikli_ortalama_vade_gun": self.avg_days_weighted,
            "vade_dagilimi": self.buckets,
            "aylik_tahsilat": self.monthly,
        }


def _bucket_key(days: int) -> str:
    for key, _label, lo, hi in VADE_ARALIKLARI:
        if (lo is None or days >= lo) and (hi is None or days <= hi):
            return key
    raise AssertionError("ulaşılamaz")


def summarize_portfolio(
    items: Iterable[PortfolioItem], valuation_date: Optional[date] = None
) -> PortfolioSummary:
    """Portföy toplamlarını hesaplar.

    Toplamlar, satırlarda gösterilen kuruşa yuvarlanmış değerlerin toplamıdır;
    böylece tablo ile toplam satırı birebir tutar. Ortalama vadede vadesi
    geçmiş evraklar 0 gün kabul edilir.
    """
    vdate = valuation_date or today_tr()
    vals: list[tuple[PortfolioItem, Valuation]] = []
    for it in items:
        vals.append((it, value_document(it.nominal, it.maturity_date, it.annual_rate_pct, it.method, vdate)))

    zero = Decimal("0.00")
    total_fv = sum((v.nominal for _, v in vals), zero)
    total_pv = sum((v.present_value for _, v in vals), zero)
    total_cost = total_fv - total_pv

    with localcontext(FIN_CONTEXT):
        if vals:
            days_list = [max(v.days, 0) for _, v in vals]
            avg_simple = round_pct(Decimal(sum(days_list)) / Decimal(len(vals)), 1)
            avg_weighted = round_pct(
                sum((Decimal(max(v.days, 0)) * v.nominal for _, v in vals), Decimal(0)) / total_fv, 1
            )
            loss = round_pct(total_cost / total_fv * YUZ)
        else:
            avg_simple = avg_weighted = None
            loss = Decimal(0)

    buckets = OrderedDict(
        (key, {"anahtar": key, "etiket": label, "adet": 0, "nominal": zero, "bugunku_deger": zero})
        for key, label, _lo, _hi in VADE_ARALIKLARI
    )
    monthly: dict[str, dict] = {}
    for _it, v in vals:
        b = buckets[_bucket_key(v.days)]
        b["adet"] += 1
        b["nominal"] += v.nominal
        b["bugunku_deger"] += v.present_value
        key = f"{v.maturity_date.year:04d}-{v.maturity_date.month:02d}"
        m = monthly.setdefault(
            key,
            {
                "ay": key,
                "etiket": f"{AY_ADLARI[v.maturity_date.month - 1]} {v.maturity_date.year}",
                "adet": 0,
                "nominal": zero,
                "bugunku_deger": zero,
            },
        )
        m["adet"] += 1
        m["nominal"] += v.nominal
        m["bugunku_deger"] += v.present_value

    return PortfolioSummary(
        valuation_date=vdate,
        count=len(vals),
        total_nominal=total_fv,
        total_present_value=total_pv,
        total_time_cost=total_cost,
        loss_pct=loss,
        avg_days_simple=avg_simple,
        avg_days_weighted=avg_weighted,
        buckets=list(buckets.values()),
        monthly=[monthly[k] for k in sorted(monthly)],
        valuations=vals,
    )
