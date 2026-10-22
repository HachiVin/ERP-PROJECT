import json

import pandas as pd
import pytest

from erp_dashboard import config, loaders
from erp_dashboard.modules import MODULES

# Row counts of the bundled dummy data (inventory and purchase are flattened to one row per line).
EXPECTED_ROWS = {
    "CRM": 12,
    "Sales": 100,
    "Finance": 24,
    "Inventory": 48,
    "Purchase": 14,
    "Payment": 17,
    "Partners": 9,
    "Products": 5,
    "Credit": 6,
    "HR": 8,
    "GA": 16,
}


def write_json(directory, filename, payload) -> None:
    (directory / filename).write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.parametrize("spec", MODULES, ids=lambda spec: spec.name)
def test_bundled_data_loads_with_expected_row_count(spec):
    df = spec.load(config.FISTX_DATA_DIR)
    assert len(df) == EXPECTED_ROWS[spec.name]
    assert not df.columns.empty


def test_every_module_has_expected_row_count_entry():
    assert {spec.name for spec in MODULES} == set(EXPECTED_ROWS)


def test_crm_columns_and_types():
    df = loaders.load_crm(config.FISTX_DATA_DIR)
    assert list(df.columns) == [
        "ID",
        "Opportunity",
        "Stage",
        "Revenue",
        "Probability",
        "Customer",
        "Salesperson",
        "Created",
    ]
    assert pd.api.types.is_datetime64_any_dtype(df["Created"])


def test_sales_columns_and_types():
    df = loaders.load_sales(config.FISTX_DATA_DIR)
    assert list(df.columns) == ["SO Number", "Customer", "Date", "Salesperson", "Amount", "Status"]
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])


def test_missing_file_is_reported(tmp_path):
    with pytest.raises(loaders.DataLoadError, match="tidak ditemukan"):
        loaders.load_crm(tmp_path)


def test_invalid_json_is_reported(tmp_path):
    (tmp_path / "crm.json").write_text("{bukan json", encoding="utf-8")
    with pytest.raises(loaders.DataLoadError, match="Gagal membaca"):
        loaders.load_crm(tmp_path)


def test_json_that_is_not_a_list_is_reported(tmp_path):
    write_json(tmp_path, "crm.json", {"id": 1})
    with pytest.raises(loaders.DataLoadError, match="daftar"):
        loaders.load_crm(tmp_path)


def test_malformed_record_is_reported_instead_of_crashing(tmp_path):
    write_json(tmp_path, "crm.json", [{"id": 1, "partner_id": "bukan-objek"}])
    with pytest.raises(loaders.DataLoadError, match="tidak sesuai"):
        loaders.load_crm(tmp_path)


def test_empty_file_gives_an_empty_frame(tmp_path):
    write_json(tmp_path, "crm.json", [])
    assert loaders.load_crm(tmp_path).empty


def test_missing_related_names_default_to_unknown(tmp_path):
    write_json(tmp_path, "crm.json", [{"id": 1, "create_date": "2025-01-02"}])
    row = loaders.load_crm(tmp_path).iloc[0]
    assert row["Customer"] == "Unknown"
    assert row["Salesperson"] == "Unknown"
    assert row["Stage"] == "Unknown"


def test_rows_with_unparseable_dates_are_dropped(tmp_path):
    write_json(
        tmp_path,
        "crm.json",
        [{"id": 1, "create_date": "2025-01-02"}, {"id": 2, "create_date": "bukan tanggal"}],
    )
    df = loaders.load_crm(tmp_path)
    assert list(df["ID"]) == [1]


def test_payments_with_unparseable_dates_are_kept(tmp_path):
    write_json(tmp_path, "payment.json", [{"id": 1, "date": "bukan tanggal"}])
    df = loaders.load_payment(tmp_path)
    assert len(df) == 1
    assert pd.isna(df.iloc[0]["Date"])


def test_inventory_is_flattened_to_one_row_per_move_line(tmp_path):
    write_json(
        tmp_path,
        "inventory.json",
        [
            {
                "reference": "WH/OUT/1",
                "scheduled_date": "2025-02-03",
                "move_line_ids": [
                    {"product_id": {"name": "A"}, "product_uom_qty": 2},
                    {"product_id": {"name": "B"}, "product_uom_qty": 5},
                ],
            },
            {"reference": "WH/OUT/2", "scheduled_date": "2025-02-04", "move_line_ids": []},
        ],
    )
    df = loaders.load_inventory(tmp_path)
    assert list(df["Product"]) == ["A", "B"]
    assert list(df["Quantity"]) == [2, 5]


def test_purchase_is_flattened_to_one_row_per_order_line(tmp_path):
    write_json(
        tmp_path,
        "purchase.json",
        [
            {
                "name": "PO1",
                "date_order": "2025-03-01",
                "order_line": [
                    {"product_id": {"name": "A"}, "product_qty": 1},
                    {"product_id": {"name": "B"}, "product_qty": 3},
                ],
            }
        ],
    )
    df = loaders.load_purchase(tmp_path)
    assert list(df["Product"]) == ["A", "B"]
    assert set(df["PO Number"]) == {"PO1"}
