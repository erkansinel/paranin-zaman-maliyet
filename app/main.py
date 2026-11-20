"""Uygulama giriş noktası.

Çalıştırma:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import accounts, calc, documents
from .db import Base, engine
from .finance import ValidationError

STATIC = Path(__file__).resolve().parent / "static"



@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)  # tablolar yoksa oluşturulur
    yield


app = FastAPI(title="Paranın Zaman Maliyeti", version="1.0.0", lifespan=lifespan,
              docs_url="/api/belgeler", redoc_url=None, openapi_url="/api/openapi.json")


@app.exception_handler(ValidationError)
async def _validation_error(_req: Request, exc: ValidationError):
    return JSONResponse({"detail": exc.message, "alan": exc.field}, status_code=422)


@app.exception_handler(RequestValidationError)
async def _request_validation_error(_req: Request, exc: RequestValidationError):
    errs = exc.errors()
    field = str(errs[0]["loc"][-1]) if errs else ""
    return JSONResponse({"detail": f"Eksik veya hatalı alan: {field}", "alan": field}, status_code=422)


@app.exception_handler(StarletteHTTPException)
async def _http_error(_req: Request, exc: StarletteHTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.get("/api/saglik")
def health():
    return {"durum": "calisiyor"}


app.include_router(accounts.router)
app.include_router(calc.router)
app.include_router(documents.router)

app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
