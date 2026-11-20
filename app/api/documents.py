"""Firma portföyü: evrak kayıtları, portföy özeti ve dışa aktarma."""

from __future__ import annotations

import csv
import io
from datetime import date
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..finance import (
    Method,
    PortfolioItem,
    ValidationError,
    summarize_portfolio,
    today_tr,
    value_document,
)
from ..finance.discount import validate_amount, validate_dates, validate_rate_pct
from ..models import Document, User
from ..security import accessible_company, current_user
from .common import not_found, ok, parse_date, parse_method

router = APIRouter(prefix="/api/firmalar/{company_id}", tags=["portföy"])

DURUMLAR = {"portfoyde": "Portföyde", "tahsil_edildi": "Tahsil edildi", "iade": "İade / karşılıksız"}


class DocumentIn(BaseModel):
    evrak_no: str
    muhatap: str
    evrak_turu: str = "cek"
    nominal: str
    duzenleme_tarihi: Optional[str] = None
    vade_tarihi: str
    yillik_oran: str
    yontem: str = "bilesik"
    durum: str = "portfoyde"
    banka: Optional[str] = None
    notlar: Optional[str] = None


def _apply(doc: Document, body: DocumentIn) -> None:
    if not body.evrak_no.strip():
        raise ValidationError("evrak_no", "Evrak numarası zorunludur.")
    if not body.muhatap.strip():
        raise ValidationError("muhatap", "Müşteri / firma adı zorunludur.")
    if body.evrak_turu not in ("cek", "senet"):
        raise ValidationError("evrak_turu", "Evrak türü çek veya senet olmalıdır.")
    if body.durum not in DURUMLAR:
        raise ValidationError("durum", "Geçersiz evrak durumu.")
    issue = parse_date(body.duzenleme_tarihi, "duzenleme_tarihi", required=False)
    maturity = parse_date(body.vade_tarihi, "vade_tarihi")
    validate_dates(issue, maturity)
    doc.doc_no = body.evrak_no.strip()[:60]
    doc.counterparty = body.muhatap.strip()[:200]
    doc.doc_type = body.evrak_turu
    doc.nominal = validate_amount(body.nominal)
    doc.issue_date = issue
    doc.maturity_date = maturity
    doc.annual_rate = validate_rate_pct(body.yillik_oran)
    doc.method = parse_method(body.yontem).value
    doc.status = body.durum
    doc.bank = (body.banka or "").strip()[:120] or None
    doc.notes = (body.notlar or "").strip() or None
    v = value_document(doc.nominal, doc.maturity_date, doc.annual_rate, Method(doc.method))
    doc.pv_snapshot = v.present_value
    doc.cost_snapshot = v.time_cost
    doc.snapshot_date = v.valuation_date


def doc_dict(d: Document, asof: date, rate_override=None) -> dict:
    rate = rate_override if rate_override is not None else d.annual_rate
    v = value_document(d.nominal, d.maturity_date, rate, Method(d.method), asof)
    return {
        "id": d.id,
        "evrak_no": d.doc_no,
        "muhatap": d.counterparty,
        "evrak_turu": d.doc_type,
        "nominal": d.nominal,
        "duzenleme_tarihi": d.issue_date,
        "vade_tarihi": d.maturity_date,
        "yillik_oran": d.annual_rate,
        "yontem": d.method,
        "durum": d.status,
        "durum_adi": DURUMLAR.get(d.status, d.status),
        "banka": d.bank,
        "notlar": d.notes,
        "kayit_degeri": {"tarih": d.snapshot_date, "bugunku_deger": d.pv_snapshot, "zaman_maliyeti": d.cost_snapshot},
        "guncel": v.as_dict(),
    }


def _asof(tarih: Optional[str]) -> date:
    return parse_date(tarih, "tarih", required=False) or today_tr()


@router.get("/evraklar")
def list_documents(company_id: int, durum: Optional[str] = None, tarih: Optional[str] = None,
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    accessible_company(company_id, db, user)
    q = db.query(Document).filter(Document.company_id == company_id)
    if durum:
        q = q.filter(Document.status == durum)
    asof = _asof(tarih)
    return ok([doc_dict(d, asof) for d in q.order_by(Document.maturity_date, Document.id).all()])


@router.post("/evraklar")
def create_document(company_id: int, body: DocumentIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    accessible_company(company_id, db, user)
    d = Document(company_id=company_id, created_by=user.id)
    _apply(d, body)
    db.add(d)
    _commit_unique(db)
    return ok(doc_dict(d, today_tr()), 201)


@router.put("/evraklar/{doc_id}")
def update_document(company_id: int, doc_id: int, body: DocumentIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    accessible_company(company_id, db, user)
    d = db.get(Document, doc_id)
    if d is None or d.company_id != company_id:
        raise not_found("Evrak")
    _apply(d, body)
    _commit_unique(db)
    return ok(doc_dict(d, today_tr()))


@router.delete("/evraklar/{doc_id}")
def delete_document(company_id: int, doc_id: int, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    accessible_company(company_id, db, user)
    d = db.get(Document, doc_id)
    if d is None or d.company_id != company_id:
        raise not_found("Evrak")
    db.delete(d)
    db.commit()
    return ok({"tamam": True})


def _commit_unique(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValidationError("evrak_no", "Bu firmada aynı türde ve numarada bir evrak zaten kayıtlı.")


@router.get("/portfoy")
def portfolio(company_id: int, tarih: Optional[str] = None, oran: Optional[str] = None,
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Portföydeki (tahsil edilmemiş) evrakların güncel özeti.

    ``oran`` verilirse tüm evraklar bu tek oranla yeniden değerlenir (senaryo analizi).
    """
    company = accessible_company(company_id, db, user)
    asof = _asof(tarih)
    rate_override = validate_rate_pct(oran, "oran") if oran not in (None, "") else None
    docs = db.query(Document).filter(Document.company_id == company_id,
                                     Document.status == "portfoyde").order_by(Document.maturity_date).all()
    items = [PortfolioItem(d.nominal, d.maturity_date,
                           rate_override if rate_override is not None else d.annual_rate,
                           Method(d.method), ref=d.id) for d in docs]
    s = summarize_portfolio(items, asof)
    out = s.as_dict()
    out["firma"] = company.name
    out["senaryo_orani"] = rate_override
    out["evraklar"] = [doc_dict(d, asof, rate_override) for d in docs]
    by_type = {}
    for d, (_it, v) in zip(docs, s.valuations):
        t = by_type.setdefault(d.doc_type, {"tur": d.doc_type, "adet": 0, "nominal": 0, "bugunku_deger": 0})
        t["adet"] += 1
        t["nominal"] += v.nominal
        t["bugunku_deger"] += v.present_value
    out["tur_dagilimi"] = list(by_type.values())
    return ok(out)


@router.get("/disa-aktar.csv")
def export_csv(company_id: int, tarih: Optional[str] = None, user: User = Depends(current_user),
               db: Session = Depends(get_db)):
    """Excel'de doğrudan açılabilen (UTF-8 BOM, noktalı virgül ayraçlı) CSV."""
    company = accessible_company(company_id, db, user)
    asof = _asof(tarih)
    docs = db.query(Document).filter(Document.company_id == company_id).order_by(Document.maturity_date).all()
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["Firma", company.name, "Değerleme tarihi", asof.strftime("%d.%m.%Y")])
    w.writerow([])
    w.writerow(["Evrak No", "Tür", "Müşteri/Firma", "Durum", "Nominal (TL)", "Düzenleme", "Vade",
                "Kalan Gün", "Yıllık Oran (%)", "Yöntem", "Bugünkü Değer (TL)", "Zaman Maliyeti (TL)",
                "Değer Kaybı (%)"])

    def tr(x) -> str:
        return format(x, "f").replace(".", ",")

    for d in docs:
        v = value_document(d.nominal, d.maturity_date, d.annual_rate, Method(d.method), asof)
        w.writerow([d.doc_no, "Çek" if d.doc_type == "cek" else "Senet", d.counterparty,
                    DURUMLAR.get(d.status, d.status), tr(d.nominal),
                    d.issue_date.strftime("%d.%m.%Y") if d.issue_date else "",
                    d.maturity_date.strftime("%d.%m.%Y"), v.days, tr(d.annual_rate),
                    Method(d.method).label, tr(v.present_value), tr(v.time_cost), tr(v.loss_pct)])
    data = "﻿" + buf.getvalue()
    name = "".join(ch if ch.isalnum() else "_" for ch in company.name)[:40]
    fname = f"portfoy_{name}_{asof.isoformat()}.csv"
    ascii_name = fname.encode("ascii", "replace").decode().replace("?", "_")
    disp = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(fname)}"
    return Response(data.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": disp})
