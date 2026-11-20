"""Örnek veri yükleyici.

Kullanım:  python -m app.demo  [--kullanici demo --parola demo1234]

Boş bir veritabanına bir yönetici, iki örnek firma ve vadeleri bugüne göre
dağıtılmış örnek çek/senetler ekler. Var olan kayıtlara dokunmaz.
"""

from __future__ import annotations

import argparse
from datetime import timedelta
from decimal import Decimal

from .db import Base, SessionLocal, engine
from .finance import Method, today_tr, value_document
from .models import Company, Document, User
from .security import hash_password

ORNEK = [
    # evrak no, muhatap, tür, tutar, gün, oran, yöntem
    ("CK-24001", "Yıldız Konfeksiyon Ltd.", "cek", "1000000", 240, "40", "bilesik"),
    ("CK-24002", "Ege İplik San. A.Ş.", "cek", "350000", 45, "40", "bilesik"),
    ("CK-24003", "Marmara Boya Kimya", "cek", "180000", 12, "40", "bilesik"),
    ("SN-1101", "Anadolu Tekstil Paz.", "senet", "420000", 95, "42", "bilesik"),
    ("CK-24004", "Kuzey Lojistik A.Ş.", "cek", "275500.50", 150, "40", "bilesik"),
    ("CK-24005", "Yıldız Konfeksiyon Ltd.", "cek", "600000", 300, "40", "bilesik"),
    ("SN-1102", "Bursa Örme Sanayi", "senet", "95000", 0, "40", "bilesik"),
    ("CK-24006", "Ege İplik San. A.Ş.", "cek", "130000", -8, "40", "bilesik"),
    ("CK-24007", "Delta Perakende", "cek", "760000", 400, "38", "bilesik"),
    ("SN-1103", "Akdeniz Moda Ltd.", "senet", "210000", 60, "45", "basit"),
    ("CK-24008", "Kuzey Lojistik A.Ş.", "cek", "490000", 200, "40", "bilesik"),
    ("CK-24009", "Marmara Boya Kimya", "cek", "155000", 120, "40", "bilesik"),
]


def run(username: str, password: str) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user is None:
            user = User(username=username, full_name="Demo Yönetici", is_admin=True,
                        password_hash=hash_password(password))
            db.add(user)
        if db.query(Company).filter_by(name="Örnek Tekstil A.Ş.").first() is None:
            c1 = Company(name="Örnek Tekstil A.Ş.", tax_no="1234567890", default_rate=Decimal("40"))
            c2 = Company(name="Örnek Gıda Dağıtım Ltd.", default_rate=Decimal("45"))
            db.add_all([c1, c2])
            db.flush()
            today = today_tr()
            for no, who, typ, amt, days, rate, method in ORNEK:
                mat = today + timedelta(days=days)
                v = value_document(amt, mat, rate, Method(method), today)
                db.add(Document(company_id=c1.id, doc_no=no, counterparty=who, doc_type=typ,
                                nominal=Decimal(amt), issue_date=today - timedelta(days=10),
                                maturity_date=mat, annual_rate=Decimal(rate), method=method,
                                pv_snapshot=v.present_value, cost_snapshot=v.time_cost,
                                snapshot_date=today, created_by=None))
            for i, (amt, days) in enumerate([("250000", 30), ("400000", 90), ("150000", 180)], 1):
                mat = today + timedelta(days=days)
                v = value_document(amt, mat, "45", Method.COMPOUND, today)
                db.add(Document(company_id=c2.id, doc_no=f"GD-{i:03d}", counterparty="Market Zinciri A.Ş.",
                                doc_type="cek", nominal=Decimal(amt), maturity_date=mat,
                                annual_rate=Decimal("45"), method="bilesik", pv_snapshot=v.present_value,
                                cost_snapshot=v.time_cost, snapshot_date=today))
        db.commit()
        print(f"Örnek veri hazır. Giriş: {username} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Örnek veri yükle")
    p.add_argument("--kullanici", default="demo")
    p.add_argument("--parola", default="demo1234")
    a = p.parse_args()
    run(a.kullanici.lower(), a.parola)
