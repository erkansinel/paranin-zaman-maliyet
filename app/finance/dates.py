"""Tarih hesapları: gerçek gün sayısı (ACT) ve takvim ayı + gün ayrıştırması."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone

#: Türkiye 2016'dan beri sabit UTC+3 kullanır (yaz saati uygulaması yok).
TURKIYE_SAATI = timezone(timedelta(hours=3), name="TRT")


def today_tr() -> date:
    """Türkiye saatine göre bugünün tarihi."""
    return datetime.now(TURKIYE_SAATI).date()


def actual_days(start: date, end: date) -> int:
    """İki tarih arasındaki gerçek takvim günü sayısı (artık yıllar dahil).

    Vade başlangıçtan önceyse sonuç negatiftir.
    """
    return (end - start).days


def add_months(d: date, months: int) -> date:
    """Tarihe takvim ayı ekler; ay sonu taşmalarında ayın son gününe sabitler.

    Örnek: 31 Ocak + 1 ay = 28/29 Şubat.
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def months_and_days(start: date, end: date) -> tuple[int, int]:
    """Başlangıçtan vadeye kalan süreyi "X ay Y gün" olarak ayrıştırır.

    Tam takvim ayları sayılır, kalan kısım gün olarak verilir. Vade geçmişse
    (end < start) değerler negatif işaretle döner.
    """
    if end < start:
        m, dd = months_and_days(end, start)
        return -m, -dd
    months = 0
    while add_months(start, months + 1) <= end:
        months += 1
    days = (end - add_months(start, months)).days
    return months, days
