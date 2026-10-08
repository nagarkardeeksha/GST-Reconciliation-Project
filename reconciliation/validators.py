TWO_B_REQUIRED_COLUMNS = [
    '2B MONTH',
    'TYPE',
    'GSTIN of supplier',
    'Trade/Legal name',
    'Invoice number',
    'Invoice type',
    'Invoice Date',
    'Invoice Value(₹)',
    'Place of supply',
    'Supply Attract Reverse Charge',
    'Taxable Value (₹)',
    'Integrated Tax(₹)',
    'Central Tax(₹)',
    'State/UT Tax(₹)',
    'Cess(₹)',
    'GSTR-1/IFF/GSTR-5 Period',
    'GSTR-1/IFF/GSTR-5 Filing Date',
    'ITC Availability',
    'Reason',
    'Applicable % of Tax Rate',
    'Source',
    'IRN',
    'IRN Date'
]


PURCHASE_REQUIRED_COLUMNS = [
    'Div',
    'Booking Month',
    'Transaction Type',
    'Document Number',
    'Doc. Date',
    'Invoice Number Supplier',
    'Supplier Invoice Date',
    'Ledger Description',
    'Business Partner Name',
    'HSN Code',
    'HSN Description',
    'Taxable Amt.',
    'SGST Amount',
    'CGST Amount',
    'IGST Amount',
    'Bill Amount',
    'Net Amount',
    'Tax Rate',
    'VAT Code',
    'GST Number',
    'GST Code',
    'GST_Date',
    'Description',
    'Company Number',
    'Ledger Code',
    'BP Code',
    'Remark',
    'Remark2'
]


def validate_columns(df, required_columns):
    actual_columns = set(df.columns)

    missing_columns = [
        column
        for column in required_columns
        if column not in actual_columns
    ]

    if missing_columns:
        return False, {
            'message': 'Required columns are missing',
            'missing_columns': missing_columns
        }

    return True, None


def validate_two_b_data(df):

    # Check whether all required 2B columns exist
    valid, error = validate_columns(
        df,
        TWO_B_REQUIRED_COLUMNS
    )

    if not valid:
        return False, error

    # Check important 2B fields
    important_columns = [
        'GSTIN of supplier',
        'Invoice number',
        'Invoice Date'
    ]

    for column in important_columns:

        blank_rows = df[df[column].isna()].index.tolist()

        if blank_rows:
            return False, {
                'message': f'Blank values found in {column}',
                'blank_row_count': len(blank_rows),
                'blank_rows': blank_rows[:20]
            }

    return True, None


def validate_purchase_data(df):

    valid, error = validate_columns(
        df,
        PURCHASE_REQUIRED_COLUMNS
    )

    if not valid:
        return False, error

    important_columns = [
        'GST Number',
        'Supplier Invoice Date'
    ]

    for column in important_columns:

        blank_rows = df[df[column].isna()].index.tolist()

        if blank_rows:
            return False, {
                'message': f'Blank values found in {column}',
                'blank_row_count': len(blank_rows),
                'blank_rows': blank_rows[:20]
            }

    return True, None