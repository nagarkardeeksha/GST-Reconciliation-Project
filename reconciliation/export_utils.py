import pandas as pd
from io import BytesIO


def remove_timezone(value):
    """
    Convert timezone-aware datetime into timezone-naive datetime
    so that Excel can store it.
    """
    if value is None:
        return None

    if hasattr(value, 'tzinfo') and value.tzinfo is not None:
        return value.replace(tzinfo=None)

    return value


def export_results_to_excel(results):
    """
    Convert reconciliation results into an Excel file.
    """

    data = []

    for result in results:
        data.append({
            'ID': result.id,
            'Batch ID': result.batch.batch_id,
            'GSTIN': result.gstin,
            'Vendor Name': result.vendor_name,
            'Invoice Number': result.invoice_number,
            'Invoice Date': result.invoice_date,

            '2B Taxable Value': result.two_b_taxable_value,
            'Purchase Taxable Value': result.purchase_taxable_value,
            'Taxable Difference': result.taxable_difference,

            '2B IGST': result.two_b_igst,
            'Purchase IGST': result.purchase_igst,
            'IGST Difference': result.igst_difference,

            '2B CGST': result.two_b_cgst,
            'Purchase CGST': result.purchase_cgst,
            'CGST Difference': result.cgst_difference,

            '2B SGST': result.two_b_sgst,
            'Purchase SGST': result.purchase_sgst,
            'SGST Difference': result.sgst_difference,

            'Original Status': result.original_status,
            'Current Status': result.current_status,
            'Manual Status': result.manual_status,
            'Changed By': result.changed_by,

            'Created At': remove_timezone(result.created_at),
            'Updated At': remove_timezone(result.updated_at),
        })

    df = pd.DataFrame(data)

    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name='Reconciliation Results'
        )

    output.seek(0)

    return output