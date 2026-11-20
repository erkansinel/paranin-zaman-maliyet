"""Kurulum, giriş, kullanıcı ve firma yönetimi."""

from __future__ import annotations

import hmac
import os
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..finance import ValidationError
from ..finance.discount import validate_rate_pct
from ..models import Company, Document, User
from ..security import (
    COOKIE_ADI,
    OTURUM_SURESI,
    accessible_company,
    admin_user,
    create_session,
    current_user,
    delete_session,
    hash_password,
    validate_password,
    verify_password,
)
from .common import not_found, ok, parse_method

router = APIRouter(prefix="/api", tags=["hesaplar"])


def user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "kullanici_adi": u.username,
        "ad_soyad": u.full_name,
        "yonetici": u.is_admin,
        "aktif": u.active,
        "firmalar": [c.id for c in u.companies],
    }


def company_dict(c: Company, db: Session) -> dict:
    count = db.query(func.count(Document.id)).filter(
        Document.company_id == c.id, Document.status == "portfoyde").scalar()
    return {
        "id": c.id,
        "ad": c.name,
        "vergi_no": c.tax_no,
        "varsayilan_oran": c.default_rate,
        "varsayilan_yontem": c.default_method,
        "degerleme_esasi": c.valuation_basis,
        "evrak_sayisi": count,
    }


def _set_cookie(request: Request, response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_ADI, token, httponly=True, samesite="lax",
        secure=request.url.scheme == "https",
        max_age=int(OTURUM_SURESI.total_seconds()),
    )


# --------------------------------------------------------------------------- #
# Kurulum ve oturum
# --------------------------------------------------------------------------- #

@router.get("/kurulum")
def setup_status(db: Session = Depends(get_db)):
    return ok({"kurulum_gerekli": db.query(User).count() == 0,
               "anahtar_gerekli": bool(os.environ.get("PZM_KURULUM_ANAHTARI"))})


class SetupIn(BaseModel):
    kullanici_adi: str
    ad_soyad: str
    parola: str
    ilk_firma: Optional[str] = None
    anahtar: Optional[str] = None


@router.post("/kurulum")
def setup(body: SetupIn, request: Request, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(409, detail="Kurulum zaten tamamlanmış.")
    # İnternete açık kurulumlarda ilk yönetici hesabını yalnızca anahtarı bilen oluşturabilir.
    expected = os.environ.get("PZM_KURULUM_ANAHTARI")
    if expected and not hmac.compare_digest((body.anahtar or "").encode(), expected.encode()):
        raise HTTPException(403, detail="Kurulum anahtarı hatalı.")
    _check_username(body.kullanici_adi)
    validate_password(body.parola)
    u = User(username=body.kullanici_adi.strip().lower(), full_name=body.ad_soyad.strip() or body.kullanici_adi,
             password_hash=hash_password(body.parola), is_admin=True)
    db.add(u)
    if body.ilk_firma and body.ilk_firma.strip():
        db.add(Company(name=body.ilk_firma.strip()))
    db.commit()
    token = create_session(db, u)
    resp = ok(user_dict(u))
    _set_cookie(request, resp, token)
    return resp


class LoginIn(BaseModel):
    kullanici_adi: str
    parola: str


@router.post("/giris")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=body.kullanici_adi.strip().lower()).first()
    if u is None or not u.active or not verify_password(body.parola, u.password_hash):
        raise HTTPException(401, detail="Kullanıcı adı veya parola hatalı.")
    token = create_session(db, u)
    resp = ok(user_dict(u))
    _set_cookie(request, resp, token)
    return resp


@router.post("/cikis")
def logout(request: Request, db: Session = Depends(get_db)):
    delete_session(db, request.cookies.get(COOKIE_ADI))
    resp = ok({"tamam": True})
    resp.delete_cookie(COOKIE_ADI)
    return resp


@router.get("/ben")
def me(user: User = Depends(current_user)):
    return ok(user_dict(user))


class PasswordIn(BaseModel):
    mevcut_parola: str
    yeni_parola: str


@router.post("/ben/parola")
def change_password(body: PasswordIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(body.mevcut_parola, user.password_hash):
        raise HTTPException(422, detail="Mevcut parola hatalı.")
    validate_password(body.yeni_parola)
    user = db.merge(user)
    user.password_hash = hash_password(body.yeni_parola)
    db.commit()
    return ok({"tamam": True})


# --------------------------------------------------------------------------- #
# Firmalar
# --------------------------------------------------------------------------- #

class CompanyIn(BaseModel):
    ad: str
    vergi_no: Optional[str] = None
    varsayilan_oran: str = "40"
    varsayilan_yontem: str = "bilesik"
    degerleme_esasi: str = "bugun"


def _apply_company(c: Company, body: CompanyIn) -> None:
    name = body.ad.strip()
    if not name:
        raise ValidationError("ad", "Firma adı zorunludur.")
    if body.degerleme_esasi not in ("bugun", "teslim"):
        raise ValidationError("degerleme_esasi", "Değerleme esası 'bugun' veya 'teslim' olmalıdır.")
    c.name = name[:200]
    c.tax_no = (body.vergi_no or "").strip() or None
    c.default_rate = validate_rate_pct(body.varsayilan_oran, "varsayilan_oran")
    c.default_method = parse_method(body.varsayilan_yontem).value
    c.valuation_basis = body.degerleme_esasi


@router.get("/firmalar")
def list_companies(user: User = Depends(current_user), db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name).all() if user.is_admin else sorted(
        db.merge(user).companies, key=lambda c: c.name)
    return ok([company_dict(c, db) for c in companies])


@router.post("/firmalar")
def create_company(body: CompanyIn, _a: User = Depends(admin_user), db: Session = Depends(get_db)):
    if db.query(Company).filter(func.lower(Company.name) == body.ad.strip().lower()).first():
        raise ValidationError("ad", "Bu adla bir firma zaten var.")
    c = Company()
    _apply_company(c, body)
    db.add(c)
    db.commit()
    return ok(company_dict(c, db), 201)


@router.put("/firmalar/{company_id}")
def update_company(company_id: int, body: CompanyIn, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    c = accessible_company(company_id, db, user)
    other = db.query(Company).filter(func.lower(Company.name) == body.ad.strip().lower(),
                                     Company.id != c.id).first()
    if other:
        raise ValidationError("ad", "Bu adla bir firma zaten var.")
    _apply_company(c, body)
    db.commit()
    return ok(company_dict(c, db))


@router.delete("/firmalar/{company_id}")
def delete_company(company_id: int, _a: User = Depends(admin_user), db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if c is None:
        raise not_found("Firma")
    db.delete(c)
    db.commit()
    return ok({"tamam": True})


# --------------------------------------------------------------------------- #
# Kullanıcılar (yalnız yönetici)
# --------------------------------------------------------------------------- #

class UserIn(BaseModel):
    kullanici_adi: str
    ad_soyad: str
    parola: Optional[str] = None
    yonetici: bool = False
    aktif: bool = True
    firmalar: list[int] = []


def _check_username(name: str) -> None:
    n = name.strip()
    if len(n) < 3 or not all(ch.isalnum() or ch in "._-" for ch in n):
        raise ValidationError("kullanici_adi", "Kullanıcı adı en az 3 karakter olmalı; harf, rakam, nokta, tire içerebilir.")


@router.get("/kullanicilar")
def list_users(_a: User = Depends(admin_user), db: Session = Depends(get_db)):
    return ok([user_dict(u) for u in db.query(User).order_by(User.username).all()])


@router.post("/kullanicilar")
def create_user(body: UserIn, _a: User = Depends(admin_user), db: Session = Depends(get_db)):
    _check_username(body.kullanici_adi)
    uname = body.kullanici_adi.strip().lower()
    if db.query(User).filter_by(username=uname).first():
        raise ValidationError("kullanici_adi", "Bu kullanıcı adı alınmış.")
    validate_password(body.parola or "")
    u = User(username=uname, full_name=body.ad_soyad.strip() or uname,
             password_hash=hash_password(body.parola), is_admin=body.yonetici, active=body.aktif)
    u.companies = db.query(Company).filter(Company.id.in_(body.firmalar)).all() if body.firmalar else []
    db.add(u)
    db.commit()
    return ok(user_dict(u), 201)


@router.put("/kullanicilar/{user_id}")
def update_user(user_id: int, body: UserIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if u is None:
        raise not_found("Kullanıcı")
    if u.id == admin.id and (not body.yonetici or not body.aktif):
        raise ValidationError("yonetici", "Kendi yönetici yetkinizi veya hesabınızı kapatamazsınız.")
    u.full_name = body.ad_soyad.strip() or u.username
    u.is_admin = body.yonetici
    u.active = body.aktif
    if body.parola:
        validate_password(body.parola)
        u.password_hash = hash_password(body.parola)
    u.companies = db.query(Company).filter(Company.id.in_(body.firmalar)).all() if body.firmalar else []
    db.commit()
    return ok(user_dict(u))


@router.delete("/kullanicilar/{user_id}")
def delete_user(user_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise ValidationError("id", "Kendi hesabınızı silemezsiniz.")
    u = db.get(User, user_id)
    if u is None:
        raise not_found("Kullanıcı")
    db.delete(u)
    db.commit()
    return ok({"tamam": True})
