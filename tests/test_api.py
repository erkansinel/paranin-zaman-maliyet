"""Web API uçtan uca testleri: kurulum, yetki, firma ayrımı, hesaplama ve portföy."""

from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.finance import today_tr
from app.main import app


@pytest.fixture(scope="module")
def admin():
    import os
    with TestClient(app) as c:
        body = {"kullanici_adi": "Erkan", "ad_soyad": "Erkan S.", "parola": "gizli-parola", "ilk_firma": "Alfa A.Ş."}
        # Kurulum anahtarı tanımlıysa anahtarsız / yanlış anahtarla kurulum yapılamaz
        os.environ["PZM_KURULUM_ANAHTARI"] = "gizli-anahtar"
        try:
            r = c.get("/api/kurulum")
            assert r.json() == {"kurulum_gerekli": True, "anahtar_gerekli": True}
            assert c.post("/api/kurulum", json=body).status_code == 403
            assert c.post("/api/kurulum", json={**body, "anahtar": "yanlis"}).status_code == 403
            r = c.post("/api/kurulum", json={**body, "anahtar": "gizli-anahtar"})
        finally:
            del os.environ["PZM_KURULUM_ANAHTARI"]
        assert r.status_code == 200, r.text
        assert r.json()["yonetici"] is True
        yield c


def test_kurulum_ikinci_kez_yapilamaz(admin):
    r = admin.post("/api/kurulum", json={"kullanici_adi": "x", "ad_soyad": "x", "parola": "12345678"})
    assert r.status_code == 409


def test_oturumsuz_erisim_engellenir():
    with TestClient(app) as c:
        assert c.get("/api/firmalar").status_code == 401
        assert c.post("/api/hesap/deger", json={}).status_code in (401, 422)


def test_hatali_giris():
    with TestClient(app) as c:
        r = c.post("/api/giris", json={"kullanici_adi": "erkan", "parola": "yanlis"})
        assert r.status_code == 401
        assert "hatalı" in r.json()["detail"]


def test_tekli_hesap_tutar_metin_olarak_doner(admin):
    vade = (today_tr() + timedelta(days=240)).isoformat()
    r = admin.post("/api/hesap/deger", json={"nominal": "1000000", "vade_tarihi": vade, "yillik_oran": "40"})
    assert r.status_code == 200, r.text
    s = r.json()["sonuc"]
    assert s["bugunku_deger"] == "801522.67"  # metin; float hatası yok
    assert s["zaman_maliyeti"] == "198477.33"
    assert s["gun"] == 240
    assert r.json()["diger_yontem"]["bugunku_deger"] == "791757.05"


def test_teslim_tarihine_gore_degerleme(admin):
    r = admin.post("/api/hesap/deger", json={
        "nominal": "1000000", "duzenleme_tarihi": "2026-01-01", "vade_tarihi": "2026-08-29",
        "yillik_oran": "40", "degerleme_esasi": "teslim"})
    assert r.status_code == 200, r.text
    assert r.json()["sonuc"]["gun"] == 240
    assert r.json()["sonuc"]["bugunku_deger"] == "801522.67"


@pytest.mark.parametrize("alan,deger,beklenen", [
    ("nominal", "0", "sıfırdan büyük"),
    ("nominal", "-100", "sıfırdan büyük"),
    ("yillik_oran", "-5", "negatif"),
    ("vade_tarihi", "2026-02-30", "Geçerli bir tarih"),
])
def test_hatali_girdiler(admin, alan, deger, beklenen):
    body = {"nominal": "1000", "vade_tarihi": "2027-01-01", "yillik_oran": "40"}
    body[alan] = deger
    r = admin.post("/api/hesap/deger", json=body)
    assert r.status_code == 422
    assert beklenen in r.json()["detail"]
    assert r.json()["alan"] == alan


def test_oran_karsilastirma(admin):
    vade = (today_tr() + timedelta(days=240)).isoformat()
    r = admin.post("/api/hesap/oran-karsilastirma", json={"nominal": "1000000", "vade_tarihi": vade})
    rows = r.json()["satirlar"]
    assert [x["yillik_oran"] for x in rows] == ["25", "30", "35", "40", "45", "50"]
    assert rows[3]["bugunku_deger"] == "801522.67"


def test_pesin_vadeli(admin):
    vade = (today_tr() + timedelta(days=240)).isoformat()
    r = admin.post("/api/hesap/pesin-vadeli", json={
        "nominal": "1000000", "vade_tarihi": vade, "sermaye_maliyeti": "40", "pesin_teklif": "820000"})
    j = r.json()
    assert j["karar"] == "pesin"
    assert j["esdeger_pesin_tutar"] == "801522.67"
    assert j["avantaj"] == "18477.33"


def test_firma_ayrimi_ve_portfoy(admin):
    firmalar = admin.get("/api/firmalar").json()
    alfa = firmalar[0]["id"]
    beta = admin.post("/api/firmalar", json={"ad": "Beta Ltd.", "varsayilan_oran": "45"}).json()["id"]

    bugun = today_tr()
    evraklar = [
        ("C-001", "1000000", 240, "40"),
        ("C-002", "100000", 30, "50"),
        ("C-003", "50000", -15, "40"),  # vadesi geçmiş
        ("C-004", "25000", 0, "40"),  # bugün vadeli
    ]
    for no, tutar, gun, oran in evraklar:
        r = admin.post(f"/api/firmalar/{alfa}/evraklar", json={
            "evrak_no": no, "muhatap": "Müşteri X", "evrak_turu": "cek", "nominal": tutar,
            "vade_tarihi": (bugun + timedelta(days=gun)).isoformat(), "yillik_oran": oran})
        assert r.status_code == 201, r.text

    # aynı numara tekrar kaydedilemez
    r = admin.post(f"/api/firmalar/{alfa}/evraklar", json={
        "evrak_no": "C-001", "muhatap": "Y", "nominal": "1", "vade_tarihi": bugun.isoformat(), "yillik_oran": "1"})
    assert r.status_code == 422

    p = admin.get(f"/api/firmalar/{alfa}/portfoy").json()
    assert p["adet"] == 4
    assert Decimal(p["toplam_nominal"]) == Decimal("1175000")
    assert Decimal(p["toplam_bugunku_deger"]) == Decimal("801522.67") + Decimal("96722.33") + Decimal("75000")
    assert Decimal(p["toplam_zaman_maliyeti"]) == Decimal("1175000") - Decimal(p["toplam_bugunku_deger"])

    # senaryo: tüm portföy %30 ile
    p30 = admin.get(f"/api/firmalar/{alfa}/portfoy", params={"oran": "30"}).json()
    assert Decimal(p30["toplam_bugunku_deger"]) > Decimal(p["toplam_bugunku_deger"])

    # Beta firmasının portföyü ayrı
    assert admin.get(f"/api/firmalar/{beta}/portfoy").json()["adet"] == 0

    # Sadece Beta'ya yetkili kullanıcı Alfa'yı göremez
    r = admin.post("/api/kullanicilar", json={"kullanici_adi": "beta.muhasebe", "ad_soyad": "Beta Muhasebe",
                                              "parola": "beta-parola", "firmalar": [beta]})
    assert r.status_code == 201, r.text
    with TestClient(app) as c2:
        assert c2.post("/api/giris", json={"kullanici_adi": "beta.muhasebe", "parola": "beta-parola"}).status_code == 200
        gorunen = [f["id"] for f in c2.get("/api/firmalar").json()]
        assert gorunen == [beta]
        assert c2.get(f"/api/firmalar/{alfa}/portfoy").status_code == 403
        assert c2.get(f"/api/firmalar/{alfa}/evraklar").status_code == 403
        assert c2.post("/api/firmalar", json={"ad": "Gizli"}).status_code == 403
        assert c2.get("/api/kullanicilar").status_code == 403

    # tahsil edilen evrak portföy toplamından çıkar
    docs = admin.get(f"/api/firmalar/{alfa}/evraklar").json()
    d = next(x for x in docs if x["evrak_no"] == "C-003")
    body = {k: d[k] for k in ("evrak_no", "muhatap", "evrak_turu", "nominal", "vade_tarihi", "yillik_oran", "yontem")}
    body["durum"] = "tahsil_edildi"
    assert admin.put(f"/api/firmalar/{alfa}/evraklar/{d['id']}", json=body).status_code == 200
    assert admin.get(f"/api/firmalar/{alfa}/portfoy").json()["adet"] == 3

    # CSV dışa aktarma
    r = admin.get(f"/api/firmalar/{alfa}/disa-aktar.csv")
    assert r.status_code == 200
    text = r.content.decode("utf-8-sig")
    assert "801522,67" in text and "C-002" in text
    assert "Decisora Danışmanlık A.Ş." in text


def test_cikis(admin):
    with TestClient(app) as c:
        c.post("/api/giris", json={"kullanici_adi": "erkan", "parola": "gizli-parola"})
        assert c.get("/api/ben").status_code == 200
        c.post("/api/cikis")
        assert c.get("/api/ben").status_code == 401

