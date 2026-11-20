import os
import tempfile

# Testler gerçek veritabanına dokunmasın: geçici SQLite dosyası
_tmp = tempfile.mkdtemp(prefix="pzm_test_")
os.environ["DATABASE_URL"] = os.environ.get("PZM_TEST_DATABASE_URL") or f"sqlite:///{_tmp}/test.db"
