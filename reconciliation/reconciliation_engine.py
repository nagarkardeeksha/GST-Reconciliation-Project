import pandas as pd
from datetime import datetime

# ============================================================
# BUCKET NAMES
# ============================================================

MATCHED = 'Matched'
MISMATCH = 'Mismatch'
AMOUNT_MISMATCH = 'Amount Mismatch'
TWO_B_ONLY = '2B Only'
PURCHASE_ONLY = 'Purchase Only'


# ============================================================
# HELPER: CLEAN VALUE
# ============================================================

def clean_value(value):
    """
    Clean values before creating a composite key.

    Dates are converted into YYYY-MM-DD format
    so that different Excel date formats match correctly.
    """

    if pd.isna(value):
        return ''

    # Handle pandas datetime / Python datetime
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime('%Y-%m-%d')

    value = str(value).strip()

    if not value:
        return ''

    # Try to detect date values stored as strings
    parsed_date = pd.to_datetime(
        value,
        dayfirst=True,
        errors='coerce',
        format='mixed'
    )

    if not pd.isna(parsed_date):
        return parsed_date.strftime('%Y-%m-%d')

    return value


# ============================================================
# HELPER: CREATE COMPOSITE KEY
# ============================================================

def create_composite_key(row, fields):
    """
    Create a composite key using configured fields.

    Example:

    GSTIN + Invoice Number + Invoice Date

    becomes:

    27AETFS4220H1ZR|SAP/26-27/233|08/04/2026
    """

    values = []

    for field in fields:

        value = clean_value(row.get(field, ''))

        values.append(value)

    return '|'.join(values)


# ============================================================
# BUILD 2B KEYS
# ============================================================

def build_two_b_keys(df, fields):

    df = df.copy()

    df['composite_key'] = df.apply(
        lambda row: create_composite_key(
            row,
            fields
        ),
        axis=1
    )

    return df


# ============================================================
# BUILD PURCHASE KEYS
# ============================================================

def build_purchase_keys(df, fields):

    df = df.copy()

    df['composite_key'] = df.apply(
        lambda row: create_composite_key(
            row,
            fields
        ),
        axis=1
    )

    return df


# ============================================================
# COMPARE GST AMOUNTS
# ============================================================

def compare_amounts(two_b_row, purchase_row):

    def to_number(value):
        import pandas as pd

        if pd.isna(value):
            return 0.0

        value = str(value).strip().replace(',', '')

        if value in ('', '-', 'nan', 'None'):
            return 0.0

        return float(value)

    # 2B amounts
    two_b_igst = to_number(
        two_b_row.get('Integrated Tax(' + '\u20b9' + ')', 0)
    )
    two_b_cgst = to_number(
        two_b_row.get('Central Tax(' + '\u20b9' + ')', 0)
    )
    two_b_sgst = to_number(
        two_b_row.get('State/UT Tax(' + '\u20b9' + ')', 0)
    )
    two_b_taxable = to_number(
        two_b_row.get('Taxable Value (' + '\u20b9' + ')', 0)
    )
    # Purchase amounts
    purchase_igst = to_number(purchase_row.get('IGST Amount', 0))
    purchase_cgst = to_number(purchase_row.get('CGST Amount', 0))
    purchase_sgst = to_number(purchase_row.get('SGST Amount', 0))
    purchase_taxable = to_number(purchase_row.get('Taxable Amt.', 0))

    return {
        'two_b_igst': two_b_igst,
        'purchase_igst': purchase_igst,

        'two_b_cgst': two_b_cgst,
        'purchase_cgst': purchase_cgst,

        'two_b_sgst': two_b_sgst,
        'purchase_sgst': purchase_sgst,

        'two_b_taxable': two_b_taxable,
        'purchase_taxable': purchase_taxable,

        'igst_difference': two_b_igst - purchase_igst,
        'cgst_difference': two_b_cgst - purchase_cgst,
        'sgst_difference': two_b_sgst - purchase_sgst,
        'taxable_difference': two_b_taxable - purchase_taxable,
    }

# ============================================================
# DETERMINE BUCKET
# ============================================================

def determine_bucket(
    two_b_row,
    purchase_row,
    tolerance=0.01
):

    amounts = compare_amounts(
        two_b_row,
        purchase_row
    )

    # Check GST amount differences
    gst_match = (
        abs(amounts['igst_difference']) <= tolerance
        and
        abs(amounts['cgst_difference']) <= tolerance
        and
        abs(amounts['sgst_difference']) <= tolerance
    )

    # Check taxable amount
    taxable_match = (
        abs(amounts['taxable_difference']) <= tolerance
    )

    if gst_match and taxable_match:

        status = MATCHED

    elif gst_match and not taxable_match:

        status = AMOUNT_MISMATCH

    else:

        status = MISMATCH

    return status, amounts