"""Hesaplama uç noktaları (kayıt yapmadan anlık hesaplar)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..finance import (
    VARSAYILAN_ORANLAR,
    ValidationError,
    analyze_cash_offer,
    compare_methods,
    compare_rates,
    today_tr,
)
from ..models import User
from ..security import current_user
from .common import ok, parse_date, parse_method

router = APIRouter(prefix="/api/hesap", tags=["hesaplama"])


class ValueIn(BaseModel):
    evrak_turu: str = "cek"
    nominal: str
    duzenleme_tarihi: Optional[str] = None
    vade_tarihi: str
    yillik_oran: str
    yontem: str = "bilesik"
    # Değerleme esası: "bugun" (varsayılan), "teslim" (düzenleme/teslim tarihi) veya "ozel"
    degerleme_esasi: str = "bugun"
    degerleme_tarihi: Optional[str] = None


def _valuation_date(body: ValueIn):
    issue = parse_date(body.duzenleme_tarihi, "duzenleme_tarihi", required=False)
    if body.degerleme_esasi == "teslim":
        if issue is None:
            raise ValidationError("duzenleme_tarihi", "Teslim tarihine göre değerleme için düzenleme/teslim tarihi giriniz.")
        return issue, issue
    if body.degerleme_esasi == "ozel":
        return issue, parse_date(body.degerleme_tarihi, "degerleme_tarihi")
    return issue, today_tr()


@router.post("/deger")
def value(body: ValueIn, _u: User = Depends(current_user)):
    """Tek evrak değerlemesi; seçilen yöntemle birlikte diğer yöntemin sonucunu da döner."""
    if body.evrak_turu not in ("cek", "senet"):
        raise ValidationError("evrak_turu", "Evrak türü çek veya senet olmalıdır.")
    method = parse_method(body.yontem)
    issue, vdate = _valuation_date(body)
    maturity = parse_date(body.vade_tarihi, "vade_tarihi")
    cmp = compare_methods(body.nominal, maturity, body.yillik_oran, vdate, issue)
    chosen = cmp.compound if method.value == "bilesik" else cmp.simple
    other = cmp.simple if method.value == "bilesik" else cmp.compound
    return ok({
        "evrak_turu": body.evrak_turu,
        "sonuc": chosen.as_dict(),
        "diger_yontem": other.as_dict(),
        "yontem_farki": chosen.present_value - other.present_value,
    })


class RatesIn(BaseModel):
    nominal: str
    vade_tarihi: str
    oranlar: list[str] = Field(default_factory=lambda: [str(x) for x in VARSAYILAN_ORANLAR])
    yontem: str = "bilesik"


@router.post("/oran-karsilastirma")
def rates(body: RatesIn, _u: User = Depends(current_user)):
    maturity = parse_date(body.vade_tarihi, "vade_tarihi")
    method = parse_method(body.yontem)
    rows = compare_rates(body.nominal, maturity, body.oranlar, method)
    other = compare_rates(body.nominal, maturity, body.oranlar,
                          parse_method("basit" if method.value == "bilesik" else "bilesik"))
    out = []
    for r, o in zip(rows, other):
        d = r.as_dict()
        d["diger_yontem_bugunku_deger"] = o.present_value
        out.append(d)
    return ok({"satirlar": out})


class CashIn(BaseModel):
    nominal: str
    vade_tarihi: str
    sermaye_maliyeti: str
    pesin_teklif: str
    yontem: str = "bilesik"


@router.post("/pesin-vadeli")
def cash(body: CashIn, _u: User = Depends(current_user)):
    maturity = parse_date(body.vade_tarihi, "vade_tarihi")
    a = analyze_cash_offer(body.nominal, maturity, body.sermaye_maliyeti, body.pesin_teklif,
                           parse_method(body.yontem))
    return ok(a.as_dict())
