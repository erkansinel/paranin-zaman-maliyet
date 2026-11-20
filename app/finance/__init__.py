"""Finansal hesaplama modülü.

Arayüzden, veritabanından ve web çatısından tamamen bağımsızdır; başka bir
uygulamada (ör. Excel eklentisi, komut satırı aracı) aynen kullanılabilir.
"""

from .analysis import (
    VARSAYILAN_ORANLAR,
    CashOfferAnalysis,
    MethodComparison,
    PortfolioItem,
    PortfolioSummary,
    analyze_cash_offer,
    compare_methods,
    compare_rates,
    summarize_portfolio,
)
from .dates import actual_days, add_months, months_and_days, today_tr
from .discount import (
    Method,
    Status,
    Valuation,
    discount_factor,
    implied_annual_rate,
    present_value_exact,
    value_document,
)
from .errors import ValidationError
from .money import D, format_tl, round_money

__all__ = [
    "VARSAYILAN_ORANLAR", "CashOfferAnalysis", "MethodComparison", "PortfolioItem",
    "PortfolioSummary", "analyze_cash_offer", "compare_methods", "compare_rates",
    "summarize_portfolio", "actual_days", "add_months", "months_and_days", "today_tr",
    "Method", "Status", "Valuation", "discount_factor", "implied_annual_rate",
    "present_value_exact", "value_document", "ValidationError", "D", "format_tl",
    "round_money",
]
