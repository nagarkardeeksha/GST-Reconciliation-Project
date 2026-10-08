import pandas as pd

from reconciliation.reconciliation_engine import (
    create_composite_key,
    determine_bucket,
)

# Sample 2B row
two_b_row = pd.Series({
    'GSTIN of supplier': '27AETFS4220H1ZR',
    'Invoice number': 'SAP/26-27/233',
    'Invoice Date': '08/04/2026',

    'Integrated Tax(' + '\u20b9' + ')': 0,
    'Central Tax(' + '\u20b9' + ')': 592.20,
    'State/UT Tax(' + '\u20b9' + ')': 592.20,
    'Taxable Value (' + '\u20b9' + ')': 6580.00,
})


# Sample Purchase row
purchase_row = pd.Series({
    'GST Number': '27AETFS4220H1ZR',
    'Invoice Number Supplier': 'SAP/26-27/233',
    'Supplier Invoice Date': '08/04/2026',
    'IGST Amount': 0,
    'CGST Amount': 592.20,
    'SGST Amount': 592.20,
    'Taxable Amt.': 6580.00,
})


# Master configuration
fields = {
    'GSTIN of supplier': 'GST Number',
    'Invoice number': 'Invoice Number Supplier',
    'Invoice Date': 'Supplier Invoice Date',
}


two_b_key = create_composite_key(
    two_b_row,
    list(fields.keys())
)

purchase_key = create_composite_key(
    purchase_row,
    list(fields.values())
)


print("2B Composite Key:")
print(two_b_key)

print("\nPurchase Composite Key:")
print(purchase_key)

print("\nKeys Match:")
print(two_b_key == purchase_key)


bucket = determine_bucket(
    two_b_row,
    purchase_row
)

print("\nBucket:")
print(bucket)

