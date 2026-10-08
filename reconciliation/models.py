from django.db import models


class UploadBatch(models.Model):
    batch_id = models.CharField(
        max_length=50,
        unique=True
    )

    reconciliation_month = models.CharField(
        max_length=20
    )

    two_b_file = models.FileField(
        upload_to='two_b_file/'
    )

    purchase_file = models.FileField(
        upload_to='purchase_file/'
    )

    modified_file = models.FileField(
        upload_to='update/',
        blank=True,
        null=True
    )

    modified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    modified_by = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=30,
        default='Uploaded'
    )

    def __str__(self):
        return self.batch_id
    
class MasterConfiguration(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    two_b_fields = models.JSONField()

    purchase_fields = models.JSONField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class ReconciliationResult(models.Model):

    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name='reconciliation_results'
    )

    composite_key = models.CharField(
        max_length=500,
        db_index=True
    )

    gstin = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    vendor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    invoice_number = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    invoice_date = models.DateField(
        blank=True,
        null=True
    )

    two_b_taxable_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    purchase_taxable_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    two_b_igst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    purchase_igst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    two_b_cgst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    purchase_cgst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    two_b_sgst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    purchase_sgst = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    igst_difference = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    cgst_difference = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    sgst_difference = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    taxable_difference = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    original_status = models.CharField(
        max_length=50
    )

    current_status = models.CharField(
        max_length=50
    )

    manual_status = models.BooleanField(
        default=False
    )

    changed_by = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f'{self.batch.batch_id} - {self.invoice_number}'



class TwoBData(models.Model):
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name='two_b_data'
    )

    two_b_month = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    type = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    gstin_of_supplier = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    trade_legal_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    invoice_number = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    invoice_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    invoice_date = models.DateField(
        blank=True,
        null=True
    )

    invoice_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    place_of_supply = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reverse_charge = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    taxable_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    integrated_tax = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    central_tax = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    state_tax = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    cess = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    filing_period = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    filing_date = models.DateField(
        blank=True,
        null=True
    )

    itc_availability = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    tax_rate = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    source = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    irn = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    irn_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.batch.batch_id} - {self.invoice_number}'

class PurchaseData(models.Model):
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name='purchase_data'
    )

    div = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    booking_month = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    transaction_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    document_number = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    doc_date = models.DateField(
        blank=True,
        null=True
    )

    invoice_number_supplier = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    supplier_invoice_date = models.DateField(
        blank=True,
        null=True
    )

    ledger_description = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    business_partner_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    hsn_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    hsn_description = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    taxable_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    sgst_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    cgst_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    igst_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    bill_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    net_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    tax_rate = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    vat_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    gst_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    gst_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    gst_date = models.DateField(
        blank=True,
        null=True
    )

    description = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    company_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ledger_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    bp_code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    remark = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    remark2 = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.batch.batch_id} - {self.invoice_number_supplier}'