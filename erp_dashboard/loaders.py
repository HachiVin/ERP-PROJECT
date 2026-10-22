"""JSON (Odoo-style export) to DataFrame loaders, one per ERP module.

Every loader takes the company's data directory and returns a DataFrame. This module is free of
Streamlit imports; the UI decides how to show a ``DataLoadError``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import pandas as pd

Record = dict[str, Any]


class DataLoadError(RuntimeError):
    """A data file is missing or malformed. The message is safe to show to users."""


def _read_json(path: Path) -> list[Record]:
    if not path.exists():
        raise DataLoadError(f"File {path.name} tidak ditemukan di {path.parent}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataLoadError(f"Gagal membaca {path.name}: {exc}") from exc
    if not isinstance(data, list):
        raise DataLoadError(f"{path.name} harus berisi daftar (list) record.")
    return data


def _name_of(record: Record, key: str) -> str:
    """Name of a related Odoo record such as ``partner_id`` (``{"id": 1, "name": "..."}``)."""
    return (record.get(key) or {}).get("name", "Unknown")


def _load(
    data_dir: Path,
    filename: str,
    to_rows: Callable[[list[Record]], Iterable[Record]],
    date_column: str | None = None,
    drop_missing_dates: bool = True,
) -> pd.DataFrame:
    records = _read_json(data_dir / filename)
    try:
        df = pd.DataFrame(list(to_rows(records)))
    except (AttributeError, TypeError) as exc:
        raise DataLoadError(f"Format data di {filename} tidak sesuai: {exc}") from exc
    if df.empty:
        return df
    if date_column:
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        if drop_missing_dates:
            df = df.dropna(subset=[date_column])
    return df


# --- Row builders ---------------------------------------------------------------------
def _crm_rows(records: list[Record]) -> Iterator[Record]:
    for crm in records:
        yield {
            "ID": crm.get("id", ""),
            "Opportunity": crm.get("name", ""),
            "Stage": crm.get("stage_id", "Unknown"),
            "Revenue": crm.get("expected_revenue", 0),
            "Probability": crm.get("probability", 0),
            "Customer": _name_of(crm, "partner_id"),
            "Salesperson": _name_of(crm, "user_id"),
            "Created": crm.get("create_date"),
        }


def _sales_rows(records: list[Record]) -> Iterator[Record]:
    for order in records:
        yield {
            "SO Number": order.get("name", ""),
            "Customer": _name_of(order, "partner_id"),
            "Date": order.get("date_order"),
            "Salesperson": order.get("sales_person", "Unknown"),
            "Amount": order.get("amount_total", 0),
            "Status": order.get("state", "Unknown"),
        }


def _finance_rows(records: list[Record]) -> Iterator[Record]:
    for invoice in records:
        yield {
            "ID": invoice.get("id", ""),
            "Invoice": invoice.get("name", ""),
            "Date": invoice.get("invoice_date"),
            "Customer": _name_of(invoice, "partner_id"),
            "Untaxed": invoice.get("amount_untaxed", 0),
            "Tax": invoice.get("amount_tax", 0),
            "Total": invoice.get("amount_total", 0),
            "Payment State": invoice.get("payment_state", "Unknown"),
            "Currency": invoice.get("currency_id", "Unknown"),
            "Origin": invoice.get("invoice_origin", ""),
        }


def _inventory_rows(records: list[Record]) -> Iterator[Record]:
    for picking in records:
        for move in picking.get("move_line_ids") or []:
            yield {
                "Reference": picking.get("reference", ""),
                "Date": picking.get("scheduled_date"),
                "Customer": _name_of(picking, "partner_id"),
                "Origin": picking.get("origin", ""),
                "Picking Type": picking.get("picking_type_code", ""),
                "Product": _name_of(move, "product_id"),
                "Quantity": move.get("product_uom_qty", 0),
                "State": move.get("state", "Unknown"),
            }


def _purchase_rows(records: list[Record]) -> Iterator[Record]:
    for order in records:
        for line in order.get("order_line") or []:
            yield {
                "ID": order.get("id", ""),
                "PO Number": order.get("name", ""),
                "Date": order.get("date_order"),
                "Vendor": _name_of(order, "partner_id"),
                "Product": _name_of(line, "product_id"),
                "Quantity": line.get("product_qty", 0),
                "Price Unit": line.get("price_unit", 0),
                "Subtotal": line.get("price_subtotal", 0),
                "Amount Untaxed": order.get("amount_untaxed", 0),
                "Tax": order.get("amount_tax", 0),
                "Total": order.get("amount_total", 0),
                "Status": order.get("state", "Unknown"),
            }


def _payment_rows(records: list[Record]) -> Iterator[Record]:
    for payment in records:
        yield {
            "ID": payment.get("id", ""),
            "Payment": payment.get("name", ""),
            "Date": payment.get("date"),
            "Customer/Vendor": _name_of(payment, "partner_id"),
            "Amount": payment.get("amount", 0),
            "Currency": payment.get("currency_id", ""),
            "Type": payment.get("payment_type", ""),
            "Journal": payment.get("journal_id", ""),
            "Status": payment.get("state", ""),
            "Reference": payment.get("ref", ""),
        }


def _credit_rows(records: list[Record]) -> Iterator[Record]:
    for credit in records:
        yield {
            "ID": credit.get("id", ""),
            "Credit Ref": credit.get("name", ""),
            "Customer": _name_of(credit, "partner_id"),
            "Credit Limit": credit.get("credit_limit", 0),
            "Outstanding Amount": credit.get("outstanding_amount", 0),
            "Currency": credit.get("currency_id", "USD"),
            "Status": credit.get("status", "Unknown"),
        }


def _hr_rows(records: list[Record]) -> Iterator[Record]:
    for employee in records:
        yield {
            "ID": employee.get("id", ""),
            "Name": employee.get("name", ""),
            "Job Title": employee.get("job_title", "Unknown"),
            "Department": employee.get("department_id", "Unknown"),
            "Email": employee.get("work_email", ""),
            "Phone": employee.get("work_phone", ""),
            "Status": employee.get("status", "Unknown"),
        }


def _ga_rows(records: list[Record]) -> Iterator[Record]:
    for item in records:
        yield {
            "ID": item.get("id", ""),
            "Name": item.get("name", ""),
            "Category": item.get("category", "Unknown"),
            "Amount": item.get("amount", 0),
            "Currency": item.get("currency_id", "Unknown"),
            "Responsible": _name_of(item, "responsible_id"),
            "State": item.get("state", "Unknown"),
            "Date": item.get("date"),
        }


def _partners_rows(records: list[Record]) -> Iterator[Record]:
    for partner in records:
        yield {
            "ID": partner.get("id", ""),
            "Name": partner.get("name", ""),
            "Type": partner.get("type", "Unknown"),
        }


def _products_rows(records: list[Record]) -> Iterator[Record]:
    for product in records:
        yield {
            "ID": product.get("id", ""),
            "Name": product.get("name", ""),
            "UoM": product.get("uom", "Unit"),
            "Price": product.get("price", 0.0),
        }


# --- Public loaders -------------------------------------------------------------------
def load_crm(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "crm.json", _crm_rows, date_column="Created")


def load_sales(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "sales_orders_FisTx.json", _sales_rows, date_column="Date")


def load_finance(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "finance.json", _finance_rows, date_column="Date")


def load_inventory(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "inventory.json", _inventory_rows, date_column="Date")


def load_purchase(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "purchase.json", _purchase_rows, date_column="Date")


def load_payment(data_dir: Path) -> pd.DataFrame:
    # Unlike the other dated modules, payments with an unparseable date are kept (as NaT).
    return _load(
        data_dir, "payment.json", _payment_rows, date_column="Date", drop_missing_dates=False
    )


def load_partners(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "partners.json", _partners_rows)


def load_products(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "products.json", _products_rows)


def load_credit(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "credit.json", _credit_rows)


def load_hr(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "hr.json", _hr_rows)


def load_ga(data_dir: Path) -> pd.DataFrame:
    return _load(data_dir, "ga.json", _ga_rows, date_column="Date")
