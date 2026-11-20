"""Veritabanı bağlantısı.

Varsayılan: proje klasöründeki ``data/pzm.db`` SQLite dosyası.
Sunucu kurulumunda ``DATABASE_URL`` ortam değişkeniyle PostgreSQL
kullanılabilir (ör. ``postgresql+psycopg://kullanici:sifre@host/db``).
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

ROOT = Path(__file__).resolve().parent.parent


def _default_url() -> str:
    data_dir = Path(os.environ.get("PZM_DATA_DIR", ROOT / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'pzm.db'}"


def make_engine(url: str | None = None):
    url = url or os.environ.get("DATABASE_URL") or _default_url()
    if url.startswith("postgres://"):  # bazı barındırma servislerinin eski biçimi
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, future=True, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def _fk_on(dbapi_conn, _rec):  # SQLite'ta yabancı anahtarları etkinleştir
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return eng


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class DecimalString(TypeDecorator):
    """Tutarları ve oranları metin olarak saklar.

    SQLite'ın sayı türü kayan noktalı olduğundan kuruş hassasiyeti kaybolabilir;
    metin olarak saklamak her veritabanında birebir aynı değeri garanti eder.
    """

    impl = String(40)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return format(Decimal(value), "f")

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
