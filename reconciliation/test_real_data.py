import pandas as pd

from reconciliation.excel_utils import read_excel_file
from reconciliation.reconciliation_engine import (
    build_two_b_keys,
    build_purchase_keys,
)


# ============================================================
# CONFIGURATION
# ============================================================

TWO_B_FILE = r"D:\gst_reconciliation\2B_file.xlsx"

PURCHASE_FILE = r"D:\gst_reconciliation\Purchase_Details.xlsx"


# ============================================================
# MASTER CONFIGURATION
# ============================================================

TWO_B_FIELDS = [
    'GSTIN of supplier',
    'Invoice number',
    'Invoice Date'
]

PURCHASE_FIELDS = [
    'GST Number',
    'Invoice Number Supplier',
    'Supplier Invoice Date'
]


# ============================================================
# READ 2B FILE
# ============================================================

two_b_df, error = read_excel_file(
    TWO_B_FILE,
    header_row=4
)

if error:
    print("Error reading 2B file:")
    print(error)
    raise SystemExit


print("2B file loaded successfully")
print("2B rows:", len(two_b_df))


# ============================================================
# READ PURCHASE FILE
# ============================================================

purchase_df, error = read_excel_file(
    PURCHASE_FILE,
    header_row=5
)

if error:
    print("Error reading Purchase file:")
    print(error)
    raise SystemExit


print("Purchase file loaded successfully")
print("Purchase rows:", len(purchase_df))


# ============================================================
# BUILD COMPOSITE KEYS
# ============================================================

two_b_df = build_two_b_keys(
    two_b_df,
    TWO_B_FIELDS
)

purchase_df = build_purchase_keys(
    purchase_df,
    PURCHASE_FIELDS
)


# ============================================================
# BASIC KEY ANALYSIS
# ============================================================

two_b_keys = set(
    two_b_df['composite_key']
)

purchase_keys = set(
    purchase_df['composite_key']
)


matched_keys = (
    two_b_keys
    & purchase_keys
)

two_b_only_keys = (
    two_b_keys
    - purchase_keys
)

purchase_only_keys = (
    purchase_keys
    - two_b_keys
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n==============================")
print("RECONCILIATION KEY SUMMARY")
print("==============================")

print("2B unique keys:", len(two_b_keys))
print("Purchase unique keys:", len(purchase_keys))

print("Matched keys:", len(matched_keys))
print("2B Only keys:", len(two_b_only_keys))
print("Purchase Only keys:", len(purchase_only_keys))


# ============================================================
# SHOW SAMPLE MATCHES
# ============================================================

print("\n==============================")
print("SAMPLE MATCHED KEYS")
print("==============================")

for key in list(matched_keys)[:10]:
    print(key)


# ============================================================
# SHOW 2B ONLY
# ============================================================

print("\n==============================")
print("SAMPLE 2B ONLY")
print("==============================")

for key in list(two_b_only_keys)[:10]:
    print(key)


# ============================================================
# SHOW PURCHASE ONLY
# ============================================================

print("\n==============================")
print("SAMPLE PURCHASE ONLY")
print("==============================")

for key in list(purchase_only_keys)[:10]:
    print(key)