"""Parola özetleme ve oturum yönetimi (yalnızca Python standart kütüphanesi)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import AuthSession, Company, User

ITERASYON = 310_000
COOKIE_ADI = "pzm_oturum"
OTURUM_SURESI = timedelta(days=14)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERASYON)
    return "pbkdf2_sha256${}${}${}".format(
        ITERASYON, base64.b64encode(salt).decode(), base64.b64encode(dk).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, it, salt_b64, dk_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(it))
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except Exception:
        return False


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(422, detail="Parola en az 8 karakter olmalıdır.")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=_hash_token(token), user_id=user.id,
                       expires_at=datetime.now(timezone.utc) + OTURUM_SURESI))
    db.commit()
    return token


def delete_session(db: Session, token: Optional[str]) -> None:
    if token:
        db.query(AuthSession).filter_by(token_hash=_hash_token(token)).delete()
        db.commit()


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_ADI)
    if not token:
        raise HTTPException(401, detail="Oturum açmanız gerekiyor.")
    sess = db.get(AuthSession, _hash_token(token))
    now = datetime.now(timezone.utc)
    if sess is None:
        raise HTTPException(401, detail="Oturum süresi doldu, lütfen tekrar giriş yapın.")
    exp = sess.expires_at if sess.expires_at.tzinfo else sess.expires_at.replace(tzinfo=timezone.utc)
    if exp < now or not sess.user.active:
        db.delete(sess)
        db.commit()
        raise HTTPException(401, detail="Oturum süresi doldu, lütfen tekrar giriş yapın.")
    return sess.user


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, detail="Bu işlem için yönetici yetkisi gerekiyor.")
    return user


def accessible_company(company_id: int, db: Session, user: User) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(404, detail="Firma bulunamadı.")
    if not user.is_admin and company not in user.companies:
        raise HTTPException(403, detail="Bu firmaya erişim yetkiniz yok.")
    return company
