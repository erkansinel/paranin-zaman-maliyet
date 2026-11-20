"""Veri modeli: kullanıcılar, firmalar (portföy sahipleri) ve vadeli evraklar."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, DecimalString


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


uyelik = Table(
    "uyelik",
    Base.metadata,
    Column("kullanici_id", ForeignKey("kullanici.id", ondelete="CASCADE"), primary_key=True),
    Column("firma_id", ForeignKey("firma.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "kullanici"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    companies: Mapped[list["Company"]] = relationship(secondary=uyelik, back_populates="users")


class Company(Base):
    """Danışmanlık verilen firma. Her firmanın portföyü ayrıdır."""

    __tablename__ = "firma"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    tax_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    default_rate: Mapped[Decimal] = mapped_column(DecimalString, default=Decimal("40"))
    default_method: Mapped[str] = mapped_column(String(10), default="bilesik")
    valuation_basis: Mapped[str] = mapped_column(String(10), default="bugun")  # bugun | teslim
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    users: Mapped[list[User]] = relationship(secondary=uyelik, back_populates="companies")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", passive_deletes=True
    )


class AuthSession(Base):
    __tablename__ = "oturum"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("kullanici.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class Document(Base):
    """Portföydeki bir çek veya senet."""

    __tablename__ = "evrak"
    __table_args__ = (UniqueConstraint("firma_id", "doc_type", "doc_no", name="uq_evrak_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        "firma_id", ForeignKey("firma.id", ondelete="CASCADE"), index=True
    )
    doc_no: Mapped[str] = mapped_column(String(60))
    counterparty: Mapped[str] = mapped_column(String(200))
    doc_type: Mapped[str] = mapped_column(String(10))  # cek | senet
    nominal: Mapped[Decimal] = mapped_column(DecimalString)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    maturity_date: Mapped[date] = mapped_column(Date, index=True)
    annual_rate: Mapped[Decimal] = mapped_column(DecimalString)
    method: Mapped[str] = mapped_column(String(10), default="bilesik")
    status: Mapped[str] = mapped_column(String(20), default="portfoyde")  # portfoyde | tahsil_edildi | iade
    bank: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Kayıt anındaki değerleme (iz kaydı). Güncel değer her görüntülemede yeniden hesaplanır.
    pv_snapshot: Mapped[Decimal] = mapped_column(DecimalString)
    cost_snapshot: Mapped[Decimal] = mapped_column(DecimalString)
    snapshot_date: Mapped[date] = mapped_column(Date)

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kullanici.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company: Mapped[Company] = relationship(back_populates="documents")
