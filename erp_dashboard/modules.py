"""Registry of ERP modules: how to load each one and which views it offers.

Adding a module means adding one ``ModuleSpec`` here; the dashboard page needs no change.
Free of Streamlit imports.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from erp_dashboard import charts, loaders


@dataclass(frozen=True)
class View:
    """One entry in the "Pilih visualisasi" dropdown. ``chart=None`` means a plain table."""

    label: str
    chart: Callable[[pd.DataFrame], Figure] | None = None


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    load: Callable[[Path], pd.DataFrame]
    views: tuple[View, ...]


def _table_module(name: str, load: Callable[[Path], pd.DataFrame]) -> ModuleSpec:
    return ModuleSpec(name, load, (View(f"Data {name}"),))


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        "CRM",
        loaders.load_crm,
        (
            View("Data CRM"),
            View("Distribusi Stage", charts.crm_stage_distribution),
            View("Revenue per Salesperson", charts.crm_revenue_by_salesperson),
            View("Tren Revenue", charts.crm_revenue_trend),
        ),
    ),
    ModuleSpec(
        "Sales",
        loaders.load_sales,
        (
            View("Data Sales"),
            View("Performa Sales", charts.sales_by_salesperson),
            View("Tren Penjualan", charts.sales_trend),
            View("Distribusi Status Order", charts.sales_status_distribution),
        ),
    ),
    _table_module("Finance", loaders.load_finance),
    _table_module("Inventory", loaders.load_inventory),
    _table_module("Purchase", loaders.load_purchase),
    _table_module("Payment", loaders.load_payment),
    _table_module("Partners", loaders.load_partners),
    _table_module("Products", loaders.load_products),
    _table_module("Credit", loaders.load_credit),
    _table_module("HR", loaders.load_hr),
    _table_module("GA", loaders.load_ga),
)

MODULES_BY_NAME: dict[str, ModuleSpec] = {module.name: module for module in MODULES}
