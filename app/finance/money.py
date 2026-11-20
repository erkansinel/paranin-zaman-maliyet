"""Para ve oran yardımcıları.

Tüm finansal hesaplamalar ``decimal.Decimal`` ile, 40 haneli hassasiyette
yapılır. Kayan noktalı sayı (float) hiçbir hesaplama adımında kullanılmaz.
Yuvarlama yalnızca sonuç gösterilirken / saklanırken, kuruş (2 ondalık)
düzeyinde ve "yarım yukarı" (ROUND_HALF_UP) kuralıyla yapılır.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Context, Decimal, localcontext
from typing import Union

#: Hesaplamalarda kullanılan ondalık bağlam (40 anlamlı basamak).
FIN_CONTEXT = Context(prec=40, rounding=ROUND_HALF_UP)

KURUS = Decimal("0.01")
ORAN_HASSASIYETI = Decimal("0.000001")  # oranlar için 6 ondalık (ondalık biçimde)
YUZ = Decimal(100)
GUN_YIL = Decimal(365)

Number = Union[Decimal, int, str]


def D(value: Number) -> Decimal:
    """Değeri güvenli biçimde Decimal'e çevirir. float kabul edilmez."""
    if isinstance(value, float):
        raise TypeError("Finansal hassasiyet için float yerine str veya Decimal kullanın.")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).strip().replace(" ", ""))


def round_money(value: Decimal) -> Decimal:
    """Tutarı kuruşa (2 ondalık) yuvarlar."""
    return value.quantize(KURUS, rounding=ROUND_HALF_UP)


def round_pct(value: Decimal, places: int = 4) -> Decimal:
    """Yüzde değerini verilen ondalık sayısına yuvarlar."""
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def pct_to_decimal(pct: Number) -> Decimal:
    """%40 -> 0.40"""
    with localcontext(FIN_CONTEXT):
        return D(pct) / YUZ


def decimal_to_pct(rate: Decimal) -> Decimal:
    """0.40 -> 40"""
    with localcontext(FIN_CONTEXT):
        return rate * YUZ


def format_tl(value: Decimal) -> str:
    """Türk Lirası biçimi: 1.234.567,89 TL"""
    v = round_money(value)
    sign = "-" if v < 0 else ""
    integer, frac = f"{abs(v):.2f}".split(".")
    groups = []
    while integer:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    return f"{sign}{'.'.join(groups)},{frac} TL"


def format_pct(value: Decimal, places: int = 2) -> str:
    """Türkçe yüzde biçimi: %35,23"""
    v = round_pct(value, places)
    return "%" + f"{v:.{places}f}".replace(".", ",")
