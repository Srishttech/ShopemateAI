"""
Excel -> Pandas -> Validation -> JSON pipeline used by Admin Mode to
replace the live product catalog (data/products.json).
"""

from typing import Union
import pandas as pd

from utils import data_manager as dm

REQUIRED_COLUMNS = ["id", "name", "category", "brand", "price", "description", "rating", "stock"]


class ExcelValidationError(Exception):
    """Raised when the uploaded Excel file fails validation."""


def process_excel(file: Union[str, "bytes"]) -> dict:
    """
    Read an uploaded Excel file, validate it, convert it to the catalog
    JSON schema, and overwrite data/products.json.

    Returns a small summary dict on success. Raises ExcelValidationError
    on any validation failure (missing columns, no valid rows, etc.)
    so the caller (Streamlit Admin UI) can show a friendly error.
    """
    try:
        df = pd.read_excel(file)
    except Exception as exc:  # noqa: BLE001
        raise ExcelValidationError(f"Could not read the Excel file: {exc}") from exc

    if df.empty:
        raise ExcelValidationError("The uploaded Excel file is empty.")

    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExcelValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(REQUIRED_COLUMNS)}"
        )

    # Coerce types and drop unusable rows.
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["rating"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0)
    df["stock"] = pd.to_numeric(df.get("stock", 0), errors="coerce").fillna(0).astype(int)

    df = df.dropna(subset=["id", "name", "price"])
    df = df[df["price"] > 0]

    if df.empty:
        raise ExcelValidationError(
            "No valid product rows remained after validation. "
            "Check that 'id', 'name' and 'price' are filled in correctly."
        )

    df["id"] = df["id"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["brand"] = df["brand"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()

    products = df[REQUIRED_COLUMNS].to_dict(orient="records")

    dm.save_products(products)

    return {"count": len(products)}
