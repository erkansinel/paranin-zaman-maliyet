"""Bugünkü değer (iskonto) hesapları.

Formüller
---------
Bileşik iskonto : PV = FV / (1 + r) ** (d / 365)
Basit iskonto   : PV = FV / (1 + r * d / 365)

PV: bugünkü değer, FV: nominal (vadede tahsil edilecek) tutar,
r : yıllık iskonto oranı (ondalık, %40 -> 0.40), d: gerçek gün sayısı.

Bu modül hiçbir arayüz, veritabanı veya web çatısına bağımlı değildir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from enum import Enum
from typing import Optional

from .dates import actual_days, months_and_days
from .errors import ValidationError
from .money import (
    FIN_CONTEXT,
    GUN_YIL,
    YUZ,
    D,
    Number,
    pct_to_decimal,
    round_money,
    round_pct,
)

#: Kabul edilen en yüksek yıllık oran (%). Daha yüksek değerler büyük olasılıkla
#: yazım hatasıdır.
MAKS_YILLIK_ORAN = Decimal(1000)
#: Kabul edilen en yüksek nominal tutar (1 trilyon TL).
MAKS_TUTAR = Decimal("1000000000000")


class Method(str, Enum):
    COMPOUND = "bilesik"
    SIMPLE = "basit"

    @property
    def label(self) -> str:
        return "Bileşik iskonto" if self is Method.COMPOUND else "Basit iskonto"


class Status(str, Enum):
    ACTIVE = "vadeli"  # vadesi gelecekte
    DUE_TODAY = "bugun"  # vadesi bugün
    OVERDUE = "vadesi_gecmis"  # vadesi geçmiş


# --------------------------------------------------------------------------- #
# Doğrulama
# --------------------------------------------------------------------------- #

def validate_amount(amount: Number, field: str = "nominal") -> Decimal:
    try:
        value = D(amount)
    except (InvalidOperation, ValueError):
        raise ValidationError(field, "Tutar sayısal bir değer olmalıdır.")
    if not value.is_finite():
        raise ValidationError(field, "Tutar sayısal bir değer olmalıdır.")
    if value <= 0:
        raise ValidationError(field, "Tutar sıfırdan büyük olmalıdır.")
    if value > MAKS_TUTAR:
        raise ValidationError(field, "Tutar izin verilen üst sınırı (1 trilyon TL) aşıyor.")
    if value != round_money(value):
        raise ValidationError(field, "Tutar en fazla 2 ondalık basamak (kuruş) içerebilir.")
    return value


def validate_rate_pct(rate_pct: Number, field: str = "yillik_oran") -> Decimal:
    try:
        value = D(rate_pct)
    except (InvalidOperation, ValueError):
        raise ValidationError(field, "Oran sayısal bir değer olmalıdır.")
    if not value.is_finite():
        raise ValidationError(field, "Oran sayısal bir değer olmalıdır.")
    if value < 0:
        raise ValidationError(field, "Yıllık oran negatif olamaz.")
    if value > MAKS_YILLIK_ORAN:
        raise ValidationError(field, f"Yıllık oran en fazla %{MAKS_YILLIK_ORAN} olabilir.")
    return value


def validate_dates(issue_date: Optional[date], maturity_date: date) -> None:
    if not isinstance(maturity_date, date):
        raise ValidationError("vade_tarihi", "Geçerli bir vade tarihi giriniz.")
    if issue_date is not None and maturity_date < issue_date:
        raise ValidationError(
            "vade_tarihi", "Vade tarihi, düzenleme/teslim alma tarihinden önce olamaz."
        )


# --------------------------------------------------------------------------- #
# Çekirdek formüller (yuvarlamasız, tam hassasiyet)
# --------------------------------------------------------------------------- #

def discount_factor(rate: Decimal, days: int, method: Method) -> Decimal:
    """İskonto çarpanı: PV = FV * çarpan. ``rate`` ondalık (0.40)."""
    if days <= 0:
        return Decimal(1)
    with localcontext(FIN_CONTEXT):
        t = Decimal(days) / GUN_YIL
        if method is Method.COMPOUND:
            return Decimal(1) / ((Decimal(1) + rate) ** t)
        return Decimal(1) / (Decimal(1) + rate * t)


def present_value_exact(fv: Decimal, rate: Decimal, days: int, method: Method) -> Decimal:
    with localcontext(FIN_CONTEXT):
        return fv * discount_factor(rate, days, method)


def implied_annual_rate(fv: Decimal, pv: Decimal, days: int, method: Method) -> Optional[Decimal]:
    """Verilen PV'yi üreten yıllık oranı (ondalık) bulur (ters hesap)."""
    if days <= 0 or pv <= 0:
        return None
    with localcontext(FIN_CONTEXT):
        ratio = fv / pv
        if method is Method.COMPOUND:
            return ratio ** (GUN_YIL / Decimal(days)) - 1
        return (ratio - 1) * GUN_YIL / Decimal(days)


# --------------------------------------------------------------------------- #
# Tam değerleme sonucu
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Valuation:
    nominal: Decimal  # FV
    valuation_date: date  # değerleme (bugün) tarihi
    maturity_date: date
    days: int  # gerçek gün sayısı (negatif olabilir)
    months: int
    rem_days: int
    annual_rate_pct: Decimal
    method: Method
    status: Status
    present_value: Decimal  # kuruşa yuvarlanmış
    time_cost: Decimal  # nominal - PV (kuruş)
    loss_pct: Decimal  # nominale göre değer kaybı (%)
    period_cost_pct: Decimal  # vade boyunca PV üzerine maliyet (%) = FV/PV - 1
    effective_annual_pct: Optional[Decimal]  # yıllık efektif eşdeğer (%)
    effective_monthly_pct: Optional[Decimal]  # aylık bileşik eşdeğer (%)
    simple_monthly_pct: Decimal  # yıllık oran / 12 (%)
    present_value_exact: Decimal  # yuvarlanmamış PV (denetim için)

    def as_dict(self) -> dict:
        return {
            "nominal": self.nominal,
            "degerleme_tarihi": self.valuation_date,
            "vade_tarihi": self.maturity_date,
            "gun": self.days,
            "ay": self.months,
            "kalan_gun": self.rem_days,
            "yillik_oran": self.annual_rate_pct,
            "yontem": self.method.value,
            "yontem_adi": self.method.label,
            "durum": self.status.value,
            "bugunku_deger": self.present_value,
            "zaman_maliyeti": self.time_cost,
            "deger_kaybi_yuzde": self.loss_pct,
            "donem_maliyet_yuzde": self.period_cost_pct,
            "efektif_yillik_yuzde": self.effective_annual_pct,
            "efektif_aylik_yuzde": self.effective_monthly_pct,
            "basit_aylik_yuzde": self.simple_monthly_pct,
        }


def value_document(
    nominal: Number,
    maturity_date: date,
    annual_rate_pct: Number,
    method: Method = Method.COMPOUND,
    valuation_date: Optional[date] = None,
    issue_date: Optional[date] = None,
) -> Valuation:
    """Bir çek/senedin değerleme tarihindeki bugünkü değerini hesaplar.

    * ``valuation_date`` verilmezse bugünün (Türkiye saati) tarihi kullanılır.
    * Vadesi geçmiş veya bugün olan evrakta iskonto uygulanmaz (PV = FV),
      çünkü para artık tahsil edilebilir durumdadır; durum alanı bunu belirtir.
    """
    from .dates import today_tr

    fv = validate_amount(nominal)
    rate_pct = validate_rate_pct(annual_rate_pct)
    validate_dates(issue_date, maturity_date)
    method = Method(method)
    vdate = valuation_date or today_tr()

    days = actual_days(vdate, maturity_date)
    months, rem_days = months_and_days(vdate, maturity_date)
    status = Status.ACTIVE if days > 0 else (Status.DUE_TODAY if days == 0 else Status.OVERDUE)

    rate = pct_to_decimal(rate_pct)
    pv_exact = present_value_exact(fv, rate, days, method)
    pv = round_money(pv_exact)
    cost = fv - pv

    with localcontext(FIN_CONTEXT):
        loss_pct = cost / fv * YUZ
        if days > 0:
            ratio = fv / pv_exact
            period = (ratio - 1) * YUZ
            eff_annual = (ratio ** (GUN_YIL / Decimal(days)) - 1)
            eff_monthly = ((1 + eff_annual) ** (Decimal(1) / Decimal(12)) - 1) * YUZ
            eff_annual *= YUZ
        else:
            period = Decimal(0)
            eff_annual = None
            eff_monthly = None
        simple_monthly = rate_pct / Decimal(12)

    return Valuation(
        nominal=fv,
        valuation_date=vdate,
        maturity_date=maturity_date,
        days=days,
        months=months,
        rem_days=rem_days,
        annual_rate_pct=rate_pct,
        method=method,
        status=status,
        present_value=pv,
        time_cost=cost,
        loss_pct=round_pct(loss_pct),
        period_cost_pct=round_pct(period),
        effective_annual_pct=round_pct(eff_annual) if eff_annual is not None else None,
        effective_monthly_pct=round_pct(eff_monthly) if eff_monthly is not None else None,
        simple_monthly_pct=round_pct(simple_monthly),
        present_value_exact=pv_exact,
    )
