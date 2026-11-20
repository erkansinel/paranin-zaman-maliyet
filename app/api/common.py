"""API ortak yardımcıları: Decimal'i metin olarak koruyan JSON yanıtı ve
girdi dönüştürücüleri."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..finance import Method, ValidationError


def _default(o: Any):
    if isinstance(o, Decimal):
        # Tutarlar metin olarak gönderilir; tarayıcıda kayan nokta hatası oluşmaz.
        return format(o, "f")
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"{type(o)} JSON'a çevrilemez")


class DecimalJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(content, default=_default, ensure_ascii=False).encode("utf-8")


def ok(data: Any, status_code: int = 200) -> DecimalJSONResponse:
    return DecimalJSONResponse(data, status_code=status_code)


def parse_method(value: Optional[str]) -> Method:
    try:
        return Method(value or "bilesik")
    except ValueError:
        raise ValidationError("yontem", "Hesaplama yöntemi 'bilesik' veya 'basit' olmalıdır.")


def parse_date(value: Optional[str], field: str, required: bool = True) -> Optional[date]:
    if value in (None, ""):
        if required:
            raise ValidationError(field, "Tarih zorunludur.")
        return None
    try:
        d = date.fromisoformat(str(value))
    except ValueError:
        raise ValidationError(field, "Geçerli bir tarih giriniz (GG.AA.YYYY).")
    if not (1900 <= d.year <= 2200):
        raise ValidationError(field, "Tarih 1900-2200 aralığında olmalıdır.")
    return d


def not_found(what: str = "Kayıt") -> HTTPException:
    return HTTPException(404, detail=f"{what} bulunamadı.")
