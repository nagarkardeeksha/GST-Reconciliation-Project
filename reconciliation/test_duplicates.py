import pandas as pd

from reconciliation.excel_utils import read_excel_file
from reconciliation.models import UploadBatch
from reconciliation.reconciliation_engine import build_two_b_keys, build_purchase_keys
from reconciliation.models import MasterConfiguration


batch_id = "BATCH_20260929141819"

batch = UploadBatch.objects.get(batch_id=batch_id)
master = MasterConfiguration.objects.filter(is_active=True).first()

two_b_df, two_b_error = read_excel_file(
    batch.two_b_file.path,
    header_row=4
)

purchase_df, purchase_error = read_excel_file(
    batch.purchase_file.path,
    header_row=5
)

if two_b_error:
    print("2B ERROR:", two_b_error)
    exit()

if purchase_error:
    print("PURCHASE ERROR:", purchase_error)
    exit()

two_b_fields = list(master.two_b_fields.keys())
purchase_fields = list(master.two_b_fields.values())

two_b_df = build_two_b_keys(
    two_b_df,
    two_b_fields
)

purchase_df = build_purchase_keys(
    purchase_df,
    purchase_fields
)


# -------------------------
# 2B DUPLICATES
# -------------------------

two_b_duplicates = (
    two_b_df[
        two_b_df['composite_key'].duplicated(keep=False)
    ]
    .sort_values('composite_key')
)

print("\n==============================")
print("2B DUPLICATE INFORMATION")
print("==============================")

print("Total 2B rows:", len(two_b_df))
print("Rows involved in duplicate keys:", len(two_b_duplicates))
print(
    "Number of duplicate keys:",
    two_b_duplicates['composite_key'].nunique()
)

print("\nTop duplicate 2B keys:")

print(
    two_b_duplicates[
        ['composite_key']
    ]
    .value_counts()
    .head(20)
)


# -------------------------
# PURCHASE DUPLICATES
# -------------------------

purchase_duplicates = (
    purchase_df[
        purchase_df['composite_key'].duplicated(keep=False)
    ]
    .sort_values('composite_key')
)

print("\n==============================")
print("PURCHASE DUPLICATE INFORMATION")
print("==============================")

print("Total Purchase rows:", len(purchase_df))
print(
    "Rows involved in duplicate keys:",
    len(purchase_duplicates)
)

print(
    "Number of duplicate keys:",
    purchase_duplicates['composite_key'].nunique()
)

print("\nTop duplicate Purchase keys:")

print(
    purchase_duplicates[
        ['composite_key']
    ]
    .value_counts()
    .head(20)
)


# -------------------------
# DUPLICATES ON BOTH SIDES
# -------------------------

two_b_keys = set(
    two_b_duplicates['composite_key']
)

purchase_keys = set(
    purchase_duplicates['composite_key']
)

common_duplicate_keys = two_b_keys.intersection(
    purchase_keys
)

print("\n==============================")
print("COMMON DUPLICATE KEYS")
print("==============================")

print(
    "Duplicate keys existing in BOTH files:",
    len(common_duplicate_keys)
)

for key in list(common_duplicate_keys)[:20]:
    print("\nKEY:", key)

    print(
        "2B count:",
        len(
            two_b_df[
                two_b_df['composite_key'] == key
            ]
        )
    )

    print(
        "Purchase count:",
        len(
            purchase_df[
                purchase_df['composite_key'] == key
            ]
        )
    )