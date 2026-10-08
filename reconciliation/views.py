import logging
logger = logging.getLogger('reconciliation')
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

import json
import pandas as pd

from django.core.paginator import Paginator, EmptyPage

from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import (
    UploadBatch,
    MasterConfiguration,
    ReconciliationResult,
    TwoBData,
    PurchaseData
)
from .excel_utils import read_excel_file
from .export_utils import export_results_to_excel
from .validators import (
    validate_two_b_data,
    validate_purchase_data
)
from .reconciliation_engine import (
    build_two_b_keys,
    build_purchase_keys,
    compare_amounts,
    determine_bucket,
    TWO_B_ONLY,
    PURCHASE_ONLY
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    inline_serializer,
    OpenApiTypes,
    OpenApiParameter,
)

# ============================================================
# SESSION AUTH WITHOUT CSRF CHECK
# (keeps session login working, skips DRF's CSRF enforcement)
# ============================================================

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


def parse_invoice_date(value):

    if pd.isna(value):
        return None

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.date()

    value = str(value).strip()

    if not value:
        return None

    for date_format in [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d-%b-%y',
        '%Y-%m-%d',
        '%Y%m%d'
    ]:

        try:
            return datetime.strptime(
                value,
                date_format
            ).date()

        except ValueError:
            continue

    parsed = pd.to_datetime(
        value,
        errors='coerce'
    )

    if pd.isna(parsed):
        return None

    return parsed.date()

def parse_decimal(value):

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        value = value.replace(',', '')

    try:
        return Decimal(str(value))

    except (ValueError, TypeError, ArithmeticError):
        return None

def save_two_b_data(batch, dataframe):

    records = []

    for _, row in dataframe.iterrows():

        record = TwoBData(
            batch=batch,

            two_b_month=row.get('2B MONTH'),
            type=row.get('TYPE'),

            gstin_of_supplier=row.get(
                'GSTIN of supplier'
            ),

            trade_legal_name=row.get(
                'Trade/Legal name'
            ),

            invoice_number=row.get(
                'Invoice number'
            ),

            invoice_type=row.get(
                'Invoice type'
            ),

            invoice_date=parse_invoice_date(
                row.get('Invoice Date')
            ),

            invoice_value=parse_decimal(
                row.get('Invoice Value(₹)')
            ),

            place_of_supply=row.get(
                'Place of supply'
            ),

            reverse_charge=row.get(
                'Supply Attract Reverse Charge'
            ),

            taxable_value=parse_decimal(
                row.get('Taxable Value (₹)')
            ),

            integrated_tax=parse_decimal(
                row.get('Integrated Tax(₹)')
            ),

            central_tax=parse_decimal(
                row.get('Central Tax(₹)')
            ),

            state_tax=parse_decimal(
                row.get('State/UT Tax(₹)')
            ),

            cess=parse_decimal(
                row.get('Cess(₹)')
            ),

            filing_period=row.get(
                'GSTR-1/IFF/GSTR-5 Period'
            ),

            filing_date=parse_invoice_date(
                row.get(
                    'GSTR-1/IFF/GSTR-5 Filing Date'
                )
            ),

            itc_availability=row.get(
                'ITC Availability'
            ),

            reason=row.get(
                'Reason'
            ),

            tax_rate=row.get(
                'Applicable % of Tax Rate'
            ),

            source=row.get(
                'Source'
            ),

            irn=row.get(
                'IRN'
            ),

            irn_date=parse_invoice_date(
                row.get('IRN Date')
            )
        )

        records.append(record)

    TwoBData.objects.bulk_create(
        records,
        batch_size=1000
    )

    return len(records)

def save_purchase_data(batch, dataframe):

    records = []

    for _, row in dataframe.iterrows():

        record = PurchaseData(
            batch=batch,

            div=row.get(
                'Div'
            ),

            booking_month=row.get(
                'Booking Month'
            ),

            transaction_type=row.get(
                'Transaction Type'
            ),

            document_number=row.get(
                'Document Number'
            ),

            doc_date=parse_invoice_date(
                row.get('Doc. Date')
            ),

            invoice_number_supplier=row.get(
                'Invoice Number Supplier'
            ),

            supplier_invoice_date=parse_invoice_date(
                row.get('Supplier Invoice Date')
            ),

            ledger_description=row.get(
                'Ledger Description'
            ),

            business_partner_name=row.get(
                'Business Partner Name'
            ),

            hsn_code=row.get(
                'HSN Code'
            ),

            hsn_description=row.get(
                'HSN Description'
            ),

            taxable_amount=parse_decimal(
                row.get('Taxable Amt.')
            ),

            sgst_amount=parse_decimal(
                row.get('SGST Amount')
            ),

            cgst_amount=parse_decimal(
                row.get('CGST Amount')
            ),

            igst_amount=parse_decimal(
                row.get('IGST Amount')
            ),

            bill_amount=parse_decimal(
                row.get('Bill Amount')
            ),

            net_amount=parse_decimal(
                row.get('Net Amount')
            ),

            tax_rate=row.get(
                'Tax Rate'
            ),

            vat_code=row.get(
                'VAT Code'
            ),

            gst_number=row.get(
                'GST Number'
            ),

            gst_code=row.get(
                'GST Code'
            ),

            gst_date=parse_invoice_date(
                row.get('GST_Date')
            ),

            description=row.get(
                'Description'
            ),

            company_number=row.get(
                'Company Number'
            ),

            ledger_code=row.get(
                'Ledger Code'
            ),

            bp_code=row.get(
                'BP Code'
            ),

            remark=row.get(
                'Remark'
            ),

            remark2=row.get(
                'Remark2'
            )
        )

        records.append(record)

    PurchaseData.objects.bulk_create(
        records,
        batch_size=1000
    )

    return len(records)
# ============================================================
# TEST API
# ============================================================

def test_api(request):

    return JsonResponse({
        'success': True,
        'message': 'GST Reconciliation API is working'
    })


# ============================================================
# LOGIN API
# ============================================================
@extend_schema(
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'username': serializers.CharField(),
            'password': serializers.CharField(),
        }
    ),
    responses={
        200: inline_serializer(
            name='LoginSuccessResponse',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
                'username': serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description='Invalid or missing JSON data'),
        401: OpenApiResponse(description='Invalid username or password'),
    },
    description='Authenticate a user using username and password.'
)
@api_view(['POST'])
@authentication_classes([])
@csrf_exempt
def login_api(request):

    if request.method != 'POST':

        return JsonResponse({
            'success': False,
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        data = json.loads(request.body)

    except json.JSONDecodeError:

        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logger.warning("Login failed: username or password missing")
        return JsonResponse({
            'success': False,
            'message': 'Username and password are required'
        }, status=400)

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        logger.warning(f"Login failed: invalid credentials for username={username}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid username or password'
        }, status=401)

    login(request, user)

    logger.info(f"Login successful: username={user.username}")

    return JsonResponse({
        'success': True,
        'message': 'Login successful',
        'username': user.username
    }, status=200)


# ============================================================
# UPLOAD EXCEL API
# ============================================================
@extend_schema(
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'two_b_file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': '2B Excel file'
                },
                'purchase_file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Purchase Excel file'
                },
            },
            'required': [
                'two_b_file',
                'purchase_file'
            ],
        }
    },
    responses={
        200: OpenApiResponse(
            description='Files uploaded successfully'
        ),
        400: OpenApiResponse(
            description='Invalid files or validation error'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        500: OpenApiResponse(
            description='Database error'
        ),
    },
    description='Upload and validate the 2B and Purchase Excel files.'
)
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def upload_excel(request):

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    if not request.user.is_authenticated:

        logger.warning(
            "Unauthorized Excel upload attempt"
        )

        return JsonResponse({
            'success': False,
            'message': 'Authentication required'
        }, status=401)

    logger.info(
        "Excel upload started by user=%s",
        request.user.username
    )

    # ========================================================
    # CHECK FILES
    # ========================================================

    two_b_file = request.FILES.get(
        'two_b_file'
    )

    purchase_file = request.FILES.get(
        'purchase_file'
    )

    if not two_b_file:

        return JsonResponse({
            'success': False,
            'message': '2B Excel file is required'
        }, status=400)

    if not purchase_file:

        return JsonResponse({
            'success': False,
            'message': 'Purchase Excel file is required'
        }, status=400)

    # ========================================================
    # READ 2B EXCEL
    # ========================================================

    two_b_df, two_b_error = read_excel_file(
        two_b_file,
        header_row=4
    )

    if two_b_error:

        logger.error(
            "2B Excel read failed: %s",
            two_b_error
        )

        return JsonResponse({
            'success': False,
            'file': '2B',
            'message': 'Unable to read 2B Excel file',
            'error': two_b_error
        }, status=400)

    # ========================================================
    # READ PURCHASE EXCEL
    # ========================================================

    purchase_df, purchase_error = read_excel_file(
        purchase_file,
        header_row=5
    )

    if purchase_error:

        logger.error(
            "Purchase Excel read failed: %s",
            purchase_error
        )

        return JsonResponse({
            'success': False,
            'file': 'Purchase',
            'message': 'Unable to read Purchase Excel file',
            'error': purchase_error
        }, status=400)

    logger.info(
        "Excel files read successfully: 2B=%s rows, Purchase=%s rows",
        len(two_b_df),
        len(purchase_df)
    )

    # ========================================================
    # VALIDATE 2B
    # ========================================================

    valid, error = validate_two_b_data(
        two_b_df
    )

    if not valid:

        return JsonResponse({
            'success': False,
            'file': '2B',
            'message': error['message'],
            'details': error
        }, status=400)

    # ========================================================
    # VALIDATE PURCHASE
    # ========================================================

    valid, error = validate_purchase_data(
        purchase_df
    )

    if not valid:

        return JsonResponse({
            'success': False,
            'file': 'Purchase',
            'message': error['message'],
            'details': error
        }, status=400)

    # ========================================================
    # CREATE BATCH ID
    # ========================================================

    timestamp = datetime.now().strftime(
        '%Y%m%d%H%M%S%f'
    )[:20]

    batch_id = f'BATCH_{timestamp}'

    # ========================================================
    # SAVE EVERYTHING IN ONE TRANSACTION
    # ========================================================

    try:

        with transaction.atomic():

            # ------------------------------------------------
            # SAVE UPLOAD BATCH + ORIGINAL FILES
            # ------------------------------------------------

            batch = UploadBatch.objects.create(

                batch_id=batch_id,

                reconciliation_month=str(
                    two_b_df[
                        '2B MONTH'
                    ].iloc[0]
                ),

                two_b_file=two_b_file,

                purchase_file=purchase_file,

                status='Uploaded'
            )

            # ------------------------------------------------
            # SAVE 2B ROWS
            # ------------------------------------------------

            two_b_count = save_two_b_data(
                batch,
                two_b_df
            )

            # ------------------------------------------------
            # SAVE PURCHASE ROWS
            # ------------------------------------------------

            purchase_count = save_purchase_data(
                batch,
                purchase_df
            )

        logger.info(
            "Upload saved successfully: "
            "batch=%s, 2B rows=%s, Purchase rows=%s",
            batch.batch_id,
            two_b_count,
            purchase_count
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        return JsonResponse({

            'success': True,

            'message': (
                'Files uploaded and data stored successfully'
            ),

            'batch_id': batch.batch_id,

            'reconciliation_month':
                batch.reconciliation_month,

            'two_b_rows':
                len(two_b_df),

            'purchase_rows':
                len(purchase_df),

            'two_b_database_rows':
                two_b_count,

            'purchase_database_rows':
                purchase_count,

            'status':
                batch.status

        }, status=200)

    except Exception as e:

        logger.exception(
            "Excel upload/database save failed"
        )

        return JsonResponse({

            'success': False,

            'message': (
                'Unable to save uploaded files and data'
            ),

            'error': str(e)

        }, status=500)

# ============================================================
# MASTER CONFIGURATION API
# ============================================================
@extend_schema(
    methods=['GET'],
    responses={
        200: OpenApiResponse(
            description='Active master configuration returned successfully'
        ),
        404: OpenApiResponse(
            description='No active master configuration found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
    },
    description='Get the currently active master reconciliation configuration.'
)
@extend_schema(
    methods=['PUT'],
    request=inline_serializer(
        name='MasterConfigurationUpdateRequest',
        fields={
            'two_b_fields': serializers.JSONField(),
            'purchase_fields': serializers.JSONField(),
        }
    ),
    responses={
        200: OpenApiResponse(
            description='Master configuration updated successfully'
        ),
        400: OpenApiResponse(
            description='Invalid JSON data or required field missing'
        ),
        404: OpenApiResponse(
            description='No active master configuration found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
    },
    description='Update the active master reconciliation field mapping.'
)

@api_view(['GET', 'PUT'])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@login_required
def master_configuration_api(request):
    logger.info(
        "Master configuration request started: user=%s, method=%s",
        request.user.username,
        request.method
    )

    if request.method == 'GET':
        logger.info(
            "Master configuration GET request: user=%s",
            request.user.username
        )
        config = MasterConfiguration.objects.filter(
            is_active=True
        ).first()

        if config:
            logger.info(
                "Active master configuration found: user=%s, config_id=%s, name=%s",
                request.user.username,
                config.id,
                config.name
            )
        if not config:
            logger.warning(
                "Master configuration GET failed: no active configuration, user=%s",
                request.user.username
            )
            logger.info(
                "Master configuration fetched successfully: user=%s, config_id=%s, name=%s",
                request.user.username,
                config.id,
                config.name
            )
            return JsonResponse({
                'success': False,
                'message':
                    'No active master configuration found'
            }, status=404)

        return JsonResponse({

            'success': True,
            'configuration': {
                'id':
                    config.id,
                'name':
                    config.name,
                'two_b_fields':
                    config.two_b_fields,
                'purchase_fields':
                    config.purchase_fields,
                'is_active':
                    config.is_active,
                'created_at':
                    config.created_at,
                'updated_at':
                    config.updated_at
            }

        }, status=200)

    if request.method == 'PUT':
        logger.info(
            "Master configuration PUT request: user=%s",
            request.user.username
        )
        try:
            data = json.loads(request.body)

        except json.JSONDecodeError:
            logger.warning(
                "Master configuration update failed: invalid JSON, user=%s",
                request.user.username
            )
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)

        config = MasterConfiguration.objects.filter(
            is_active=True
        ).first()

        if config:
            logger.info(
                "Master configuration selected for update: user=%s, config_id=%s, name=%s",
                request.user.username,
                config.id,
                config.name
            )
        if not config:
            logger.warning(
                "Master configuration update failed: no active configuration, user=%s",
                request.user.username
            )
            return JsonResponse({
                'success': False,
                'message':
                    'No active master configuration found'
            }, status=404)

        two_b_fields = data.get(
            'two_b_fields'
        )
        purchase_fields = data.get(
            'purchase_fields'
        )
        if two_b_fields is None:
            logger.warning(
                "Master configuration update failed: two_b_fields missing, user=%s",
                request.user.username
            )
            return JsonResponse({
                'success': False,
                'message':
                    'two_b_fields is required'
            }, status=400)

        if purchase_fields is None:
            logger.warning(
                "Master configuration update failed: purchase_fields missing, user=%s",
                request.user.username
            )
            return JsonResponse({
                'success': False,
                'message':
                    'purchase_fields is required'
            }, status=400)

        config.two_b_fields = two_b_fields
        config.purchase_fields = purchase_fields
        config.save()

        logger.info(
            "Master configuration updated successfully: user=%s, config_id=%s, name=%s",
            request.user.username,
            config.id,
            config.name
        )
        return JsonResponse({
            'success': True,
            'message':
                'Master configuration updated successfully',
            'configuration': {
                'id':
                    config.id,
                'name':
                    config.name,
                'two_b_fields':
                    config.two_b_fields,
                'purchase_fields':
                    config.purchase_fields,
                'is_active':
                    config.is_active
            }

        }, status=200)

    return JsonResponse({

        'success': False,

        'message':
            'Only GET and PUT methods are allowed'

    }, status=405)

@extend_schema(
    request=inline_serializer(
        name='StartReconciliationRequest',
        fields={
            'batch_id': serializers.CharField(),
        }
    ),
    responses={
        200: OpenApiResponse(
            description='Reconciliation completed successfully'
        ),
        400: OpenApiResponse(
            description='Invalid JSON, missing batch ID, or master configuration error'
        ),
        404: OpenApiResponse(
            description='Batch not found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        405: OpenApiResponse(
            description='Only POST method is allowed'
        ),
    },
    description='Start GST reconciliation for an uploaded batch.'
)
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@login_required
def start_reconciliation(request):
    logger.info("Reconciliation started by user=%s", request.user.username)

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)

    batch_id = data.get('batch_id')
    logger.info(
        "Reconciliation request received: user=%s, batch_id=%s",
        request.user.username,
        batch_id
    )

    if not batch_id:
        return JsonResponse({
            'success': False,
            'message': 'batch_id is required'
        }, status=400)

    # --------------------------------------------------------
    # FIND UPLOAD BATCH
    # --------------------------------------------------------

    try:
        batch = UploadBatch.objects.get(
            batch_id=batch_id
        )
    except UploadBatch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Batch not found'
        }, status=404)

    # --------------------------------------------------------
    # GET ACTIVE MASTER CONFIGURATION
    # --------------------------------------------------------

    master = MasterConfiguration.objects.filter(
        is_active=True
    ).first()
    logger.info(
        "Active master configuration loaded: name=%s",
        master.name
    )

    if not master:
        return JsonResponse({
            'success': False,
            'message': 'Active master configuration not found'
        }, status=400)

    # --------------------------------------------------------
    # READ EXCEL FILES
    # --------------------------------------------------------

    two_b_df, two_b_error = read_excel_file(
        batch.two_b_file.path,
        header_row=4
    )

    if two_b_error:
        logger.info(
            "2B file loaded for reconciliation: batch_id=%s, rows=%s",
            batch.batch_id,
            len(two_b_df)
        )
        return JsonResponse({
            'success': False,
            'message': 'Unable to read 2B file',
            'error': two_b_error
        }, status=400)

    purchase_df, purchase_error = read_excel_file(
        batch.purchase_file.path,
        header_row=5
    )

    if purchase_error:
        logger.info(
            "Purchase file loaded for reconciliation: batch_id=%s, rows=%s",
            batch.batch_id,
            len(purchase_df)
        )
        return JsonResponse({
            'success': False,
            'message': 'Unable to read Purchase file',
            'error': purchase_error
        }, status=400)

    # --------------------------------------------------------
    # GET MASTER KEY FIELDS
    # --------------------------------------------------------

    two_b_fields = list(
        master.two_b_fields.keys()
    )

    purchase_fields = list(
        master.two_b_fields.values()
    )

    # --------------------------------------------------------
    # BUILD COMPOSITE KEYS
    # --------------------------------------------------------

    two_b_df = build_two_b_keys(
        two_b_df,
        two_b_fields
    )

    purchase_df = build_purchase_keys(
        purchase_df,
        purchase_fields
    )
    logger.info(
        "Composite keys created: batch_id=%s, 2B_rows=%s, purchase_rows=%s",
        batch.batch_id,
        len(two_b_df),
        len(purchase_df)
    )

    # --------------------------------------------------------
    # CREATE LOOKUP DICTIONARIES
    # --------------------------------------------------------

    two_b_lookup = {}

    for _, row in two_b_df.iterrows():

        key = row['composite_key']

        if not key:
            continue

        two_b_lookup.setdefault(
            key,
            []
        ).append(row)

    purchase_lookup = {}

    for _, row in purchase_df.iterrows():

        key = row['composite_key']

        if not key:
            continue

        purchase_lookup.setdefault(
            key,
            []
        ).append(row)

    # --------------------------------------------------------
    # RECONCILE
    # --------------------------------------------------------

    results = []

    all_keys = (
        set(two_b_lookup.keys())
        | set(purchase_lookup.keys())
    )

    for key in all_keys:

        two_b_rows = two_b_lookup.get(
            key,
            []
        )

        purchase_rows = purchase_lookup.get(
            key,
            []
        )

        # ----------------------------------------------------
        # BOTH FILES
        # ----------------------------------------------------

        if two_b_rows and purchase_rows:

            pair_count = min(
                len(two_b_rows),
                len(purchase_rows)
            )

            # Match available rows one-to-one
            for index in range(pair_count):

                two_b_row = two_b_rows[index]
                purchase_row = purchase_rows[index]

                status, amounts = determine_bucket(
                    two_b_row,
                    purchase_row
                )

                result = ReconciliationResult(
                    batch=batch,
                    composite_key=key,

                    gstin=str(
                        two_b_row.get(
                            'GSTIN of supplier',
                            ''
                        )
                    ),

                    vendor_name=str(
                        two_b_row.get(
                            'Trade/Legal name',
                            ''
                        )
                    ),

                    invoice_number=str(
                        two_b_row.get(
                            'Invoice number',
                            ''
                        )
                    ),

                    invoice_date=parse_invoice_date(
                        two_b_row.get('Invoice Date')
                    ),

                    two_b_taxable_value=Decimal(
                        str(amounts['two_b_taxable'])
                    ),

                    purchase_taxable_value=Decimal(
                        str(amounts['purchase_taxable'])
                    ),

                    two_b_igst=Decimal(
                        str(amounts['two_b_igst'])
                    ),

                    purchase_igst=Decimal(
                        str(amounts['purchase_igst'])
                    ),

                    two_b_cgst=Decimal(
                        str(amounts['two_b_cgst'])
                    ),

                    purchase_cgst=Decimal(
                        str(amounts['purchase_cgst'])
                    ),

                    two_b_sgst=Decimal(
                        str(amounts['two_b_sgst'])
                    ),

                    purchase_sgst=Decimal(
                        str(amounts['purchase_sgst'])
                    ),

                    igst_difference=Decimal(
                        str(amounts['igst_difference'])
                    ),

                    cgst_difference=Decimal(
                        str(amounts['cgst_difference'])
                    ),

                    sgst_difference=Decimal(
                        str(amounts['sgst_difference'])
                    ),

                    taxable_difference=Decimal(
                        str(amounts['taxable_difference'])
                    ),

                    original_status=status,
                    current_status=status,
                    manual_status=False
                )

                results.append(result)
            

            # Remaining 2B rows
            # These have no corresponding Purchase row
            if len(two_b_rows) > pair_count:

                for index in range(pair_count, len(two_b_rows)):

                    two_b_row = two_b_rows[index]

                    amounts = compare_amounts(
                        two_b_row,
                        {}
                    )

                    result = ReconciliationResult(
                        batch=batch,
                        composite_key=key,

                        gstin=str(
                            two_b_row.get(
                                'GSTIN of supplier',
                                ''
                            )
                        ),

                        vendor_name=str(
                            two_b_row.get(
                                'Trade/Legal name',
                                ''
                            )
                        ),

                        invoice_number=str(
                            two_b_row.get(
                                'Invoice number',
                                ''
                            )
                        ),

                        invoice_date=parse_invoice_date(
                            two_b_row.get('Invoice Date')
                        ),

                        two_b_taxable_value=Decimal(
                            str(amounts['two_b_taxable'])
                        ),

                        two_b_igst=Decimal(
                            str(amounts['two_b_igst'])
                        ),

                        two_b_cgst=Decimal(
                            str(amounts['two_b_cgst'])
                        ),

                        two_b_sgst=Decimal(
                            str(amounts['two_b_sgst'])
                        ),

                        original_status=TWO_B_ONLY,
                        current_status=TWO_B_ONLY,
                        manual_status=False
                    )

                    results.append(result)

            if len(purchase_rows) > pair_count:

                for index in range(pair_count, len(purchase_rows)):

                    purchase_row = purchase_rows[index]

                    amounts = compare_amounts(
                        {},
                        purchase_row
                    )

                    result = ReconciliationResult(
                        batch=batch,
                        composite_key=key,

                        gstin=str(
                            purchase_row.get(
                                'GST Number',
                                ''
                            )
                        ),

                        invoice_number=str(
                            purchase_row.get(
                                'Invoice Number Supplier',
                                ''
                            )
                        ),

                        invoice_date=parse_invoice_date(
                            purchase_row.get(
                                'Supplier Invoice Date'
                            )
                        ),

                        purchase_taxable_value=Decimal(
                            str(amounts['purchase_taxable'])
                        ),

                        purchase_igst=Decimal(
                            str(amounts['purchase_igst'])
                        ),

                        purchase_cgst=Decimal(
                            str(amounts['purchase_cgst'])
                        ),

                        purchase_sgst=Decimal(
                            str(amounts['purchase_sgst'])
                        ),

                        original_status=PURCHASE_ONLY,
                        current_status=PURCHASE_ONLY,
                        manual_status=False
                    )

                    results.append(result)

        # ----------------------------------------------------
        # 2B ONLY
        # ----------------------------------------------------

        elif two_b_rows:

            for two_b_row in two_b_rows:

                amounts = compare_amounts(
                    two_b_row,
                    {}
                )

                result = ReconciliationResult(
                    batch=batch,
                    composite_key=key,

                    gstin=str(
                        two_b_row.get(
                            'GSTIN of supplier',
                            ''
                        )
                    ),

                    vendor_name=str(
                        two_b_row.get(
                            'Trade/Legal name',
                            ''
                        )
                    ),

                    invoice_number=str(
                        two_b_row.get(
                            'Invoice number',
                            ''
                        )
                    ),

                    invoice_date=parse_invoice_date(
                        two_b_row.get('Invoice Date')
                    ),

                    two_b_taxable_value=Decimal(
                        str(amounts['two_b_taxable'])
                    ),

                    two_b_igst=Decimal(
                        str(amounts['two_b_igst'])
                    ),

                    two_b_cgst=Decimal(
                        str(amounts['two_b_cgst'])
                    ),

                    two_b_sgst=Decimal(
                        str(amounts['two_b_sgst'])
                    ),

                    original_status=TWO_B_ONLY,
                    current_status=TWO_B_ONLY,
                    manual_status=False
                )

                results.append(result)

        # ----------------------------------------------------
        # PURCHASE ONLY
        # ----------------------------------------------------

        elif purchase_rows:

            for purchase_row in purchase_rows:

                amounts = compare_amounts(
                    {},
                    purchase_row
                )

                result = ReconciliationResult(
                    batch=batch,
                    composite_key=key,

                    gstin=str(
                        purchase_row.get(
                            'GST Number',
                            ''
                        )
                    ),

                    invoice_number=str(
                        purchase_row.get(
                            'Invoice Number Supplier',
                            ''
                        )
                    ),

                    invoice_date=parse_invoice_date(
                        purchase_row.get(
                            'Supplier Invoice Date'
                        )
                    ),

                    purchase_taxable_value=Decimal(
                        str(amounts['purchase_taxable'])
                    ),

                    purchase_igst=Decimal(
                        str(amounts['purchase_igst'])
                    ),

                    purchase_cgst=Decimal(
                        str(amounts['purchase_cgst'])
                    ),

                    purchase_sgst=Decimal(
                        str(amounts['purchase_sgst'])
                    ),

                    original_status=PURCHASE_ONLY,
                    current_status=PURCHASE_ONLY,
                    manual_status=False
                )

                results.append(result)
    logger.info(
                    "Reconciliation processing completed: batch_id=%s, total_results=%s",
                    batch.batch_id,
                    len(results)
                )

    # --------------------------------------------------------
    # SAVE ALL RESULTS
    # --------------------------------------------------------

    with transaction.atomic():

        # Prevent duplicate reconciliation for same batch
        ReconciliationResult.objects.filter(
            batch=batch
        ).delete()

        ReconciliationResult.objects.bulk_create(
            results
        )

        batch.status = 'Reconciled'
        batch.save(
            update_fields=['status']
        )
        logger.info(
            "Reconciliation results saved successfully: "
            "batch_id=%s, total_results=%s, batch_status=%s",
            batch.batch_id,
            len(results),
            batch.status
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = {}

    for result in results:

        status = result.current_status

        summary[status] = (
            summary.get(status, 0) + 1
        )
    logger.info(
        "Reconciliation completed successfully: "
        "batch_id=%s, total_results=%s, summary=%s",
        batch.batch_id,
        len(results),
        summary
    )
    return JsonResponse({
        'success': True,
        'message': 'Reconciliation completed successfully',
        'batch_id': batch.batch_id,
        'total_results': len(results),
        'summary': summary
    }, status=200)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='batch_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Batch ID for which reconciliation results are required.'
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter results by reconciliation status.'
        ),
        OpenApiParameter(
            name='gstin',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter results by GSTIN.'
        ),
        OpenApiParameter(
            name='invoice_number',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter results by invoice number.'
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Page number. Default is 1.'
        ),
        OpenApiParameter(
            name='page_size',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Number of records per page. Default is 50.'
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Reconciliation results returned successfully'
        ),
        400: OpenApiResponse(
            description='Invalid parameters'
        ),
        404: OpenApiResponse(
            description='Batch not found or page out of range'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        405: OpenApiResponse(
            description='Only GET method is allowed'
        ),
    },
    description='Get reconciliation results with optional status, GSTIN, invoice number, and pagination filters.'
)
@api_view(['GET'])
@login_required
def reconciliation_results(request):

    logger.info(
        "Results request started: user=%s",
        request.user.username
    )

    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': 'Only GET method is allowed'
        }, status=405)

    batch_id = request.GET.get('batch_id')
    status = request.GET.get('status')
    gstin = request.GET.get('gstin')
    invoice_number = request.GET.get('invoice_number')

    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 50)
    logger.info(
        "Results request parameters: user=%s, batch_id=%s, status=%s, gstin=%s, invoice_number=%s, page=%s, page_size=%s",
        request.user.username,
        batch_id,
        status,
        gstin,
        invoice_number,
        page,
        page_size
    )

    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        logger.warning(
                "Invalid pagination parameters: user=%s, page=%s, page_size=%s",
                request.user.username,
                page,
                page_size
            )
        return JsonResponse({
            'success': False,
            'message': 'page and page_size must be numbers'
        }, status=400)
    print("PAGE SIZE AFTER CONVERSION:", page_size)

    if page < 1:
        logger.warning(
            "Invalid page number: user=%s, page=%s",
            request.user.username,
            page
        )
        return JsonResponse({
            'success': False,
            'message': 'page must be greater than 0'
        }, status=400)

    if page_size < 1:
        logger.warning(
            "Invalid page size: user=%s, page_size=%s",
            request.user.username,
            page_size
        )
        return JsonResponse({
            'success': False,
            'message': 'page_size must be greater than 0'
        }, status=400)

    print("GSTIN RECEIVED:", gstin)

    if not batch_id:
        logger.warning(
            "Results request failed: batch_id missing, user=%s",
            request.user.username
        )
        return JsonResponse({
            'success': False,
            'message': 'batch_id is required'
        }, status=400)

    try:
        batch = UploadBatch.objects.get(
            batch_id=batch_id
        )
        logger.info(
            "Upload batch found: batch_id=%s, current_status=%s",
            batch.batch_id,
            batch.status
        )
    except UploadBatch.DoesNotExist:
        logger.warning(
            "Results request failed: batch not found, user=%s, batch_id=%s",
            request.user.username,
            batch_id
        )
        return JsonResponse({
            'success': False,
            'message': 'Batch not found'
        }, status=404)

    # --------------------------------------------------------
    # GET RESULTS FOR BATCH
    # --------------------------------------------------------

    queryset = ReconciliationResult.objects.filter(
        batch=batch
    ).order_by('id')

    # --------------------------------------------------------
    # OPTIONAL STATUS FILTER
    # --------------------------------------------------------
    if status:
        queryset = queryset.filter(
            current_status=status
        )

    # Optional GSTIN filter
    if gstin:
        queryset = queryset.filter(
            gstin__icontains=gstin
        )

    # Optional Invoice Number filter
    if invoice_number:
        queryset = queryset.filter(
            invoice_number__icontains=invoice_number
        )

    results = list(queryset)
    logger.info(
        "Results filters applied: batch_id=%s, status=%s, gstin=%s, invoice_number=%s",
        batch_id,
        status,
        gstin,
        invoice_number
    )

    # --------------------------------------------------------
    # OPTIONAL GSTIN FILTER
    # --------------------------------------------------------

    if gstin:
        queryset = queryset.filter(
            gstin__icontains=gstin
        )

    if invoice_number:
        queryset = queryset.filter(
            invoice_number__icontains=invoice_number
        )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    total_records = queryset.count()
    logger.info(
        "Results fetched: user=%s, batch_id=%s, total_records=%s",
        request.user.username,
        batch_id,
        total_records
    )

    paginator = Paginator(
        queryset,
        page_size
    )

    try:
        page_obj = paginator.page(page)

    except EmptyPage:
        logger.warning(
            "Results page out of range: user=%s, batch_id=%s, page=%s, total_pages=%s",
            request.user.username,
            batch_id,
            page,
            paginator.num_pages
        )
        return JsonResponse({
            'success': False,
            'message': 'Page number out of range',
            'total_records': total_records,
            'total_pages': paginator.num_pages
        }, status=400)


    results = []

    for result in page_obj:
        results.append({
            'id': result.id,
            'batch_id': batch.batch_id,
            'composite_key': result.composite_key,
            'gstin': result.gstin,
            'vendor_name': result.vendor_name,
            'invoice_number': result.invoice_number,
            'invoice_date': (
                result.invoice_date.isoformat()
                if result.invoice_date
                else None
            ),

            # ------------------------------------------------
            # TAXABLE VALUES
            # ------------------------------------------------

            'two_b_taxable_value': (
                float(result.two_b_taxable_value)
                if result.two_b_taxable_value is not None
                else None
            ),

            'purchase_taxable_value': (
                float(result.purchase_taxable_value)
                if result.purchase_taxable_value is not None
                else None
            ),

            # ------------------------------------------------
            # IGST
            # ------------------------------------------------

            'two_b_igst': (
                float(result.two_b_igst)
                if result.two_b_igst is not None
                else None
            ),

            'purchase_igst': (
                float(result.purchase_igst)
                if result.purchase_igst is not None
                else None
            ),

            'igst_difference': (
                float(result.igst_difference)
                if result.igst_difference is not None
                else None
            ),

            # ------------------------------------------------
            # CGST
            # ------------------------------------------------

            'two_b_cgst': (
                float(result.two_b_cgst)
                if result.two_b_cgst is not None
                else None
            ),

            'purchase_cgst': (
                float(result.purchase_cgst)
                if result.purchase_cgst is not None
                else None
            ),

            'cgst_difference': (
                float(result.cgst_difference)
                if result.cgst_difference is not None
                else None
            ),

            # ------------------------------------------------
            # SGST
            # ------------------------------------------------

            'two_b_sgst': (
                float(result.two_b_sgst)
                if result.two_b_sgst is not None
                else None
            ),

            'purchase_sgst': (
                float(result.purchase_sgst)
                if result.purchase_sgst is not None
                else None
            ),

            'sgst_difference': (
                float(result.sgst_difference)
                if result.sgst_difference is not None
                else None
            ),

            # ------------------------------------------------
            # TAXABLE DIFFERENCE
            # ------------------------------------------------

            'taxable_difference': (
                float(result.taxable_difference)
                if result.taxable_difference is not None
                else None
            ),

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            'original_status': result.original_status,
            'current_status': result.current_status,
            'manual_status': result.manual_status,
            'changed_by': result.changed_by,

            'created_at': result.created_at.isoformat(),
            'updated_at': result.updated_at.isoformat()
        })

    print("FINAL RESULTS COUNT:", len(results))
    logger.info(
        "Results request completed successfully: user=%s, batch_id=%s, page=%s, page_size=%s, returned_records=%s",
        request.user.username,
        batch_id,
        page,
        page_size,
        len(results)
    )
    
    return JsonResponse({
        'success': True,
        'batch_id': batch.batch_id,

        'count': len(results),

        'total_records': total_records,
        'page': page,
        'page_size': page_size,
        'total_pages': paginator.num_pages,

        'results': results

    }, status=200)

@extend_schema(
    request=inline_serializer(
        name='MoveReconciliationRequest',
        fields={
            'result_id': serializers.IntegerField(
                help_text='ID of the reconciliation result to move.'
            ),
            'new_status': serializers.CharField(
                help_text='New bucket/status for the reconciliation result.'
            ),
        }
    ),
    responses={
        200: OpenApiResponse(
            description='Reconciliation result moved successfully'
        ),
        400: OpenApiResponse(
            description='Invalid JSON, missing fields, or invalid status'
        ),
        404: OpenApiResponse(
            description='Reconciliation result not found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        405: OpenApiResponse(
            description='Only POST method is allowed'
        ),
    },
    description='Manually move a reconciliation result to another reconciliation bucket.'
)
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
@login_required
def move_reconciliation(request):

    logger.info(
        "Manual reconciliation movement started by user=%s",
        request.user.username
    )

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST method is allowed'
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:

        logger.warning(
            "Manual movement failed: invalid JSON, user=%s",
            request.user.username
        )

        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)

    # --------------------------------------------------------
    # GET IDs AND NEW STATUS
    # --------------------------------------------------------

    result_id = data.get('result_id')
    result_ids = data.get('result_ids')
    new_status = data.get('new_status')

    logger.info(
        "Manual movement request: user=%s, new_status=%s, "
        "result_id=%s, result_ids=%s",
        request.user.username,
        new_status,
        result_id,
        result_ids
    )

    # --------------------------------------------------------
    # VALIDATE STATUS
    # --------------------------------------------------------

    allowed_statuses = [
        'Matched',
        'Mismatch',
        'Amount Mismatch',
        '2B Only',
        'Purchase Only'
    ]

    if not new_status:

        logger.warning(
            "Manual movement failed: new_status missing, user=%s",
            request.user.username
        )

        return JsonResponse({
            'success': False,
            'message': 'new_status is required'
        }, status=400)

    if new_status not in allowed_statuses:

        logger.warning(
            "Manual movement failed: invalid status=%s, user=%s",
            new_status,
            request.user.username
        )

        return JsonResponse({
            'success': False,
            'message': 'Invalid status',
            'allowed_statuses': allowed_statuses
        }, status=400)

    # --------------------------------------------------------
    # SUPPORT SINGLE OR MULTIPLE IDs
    # --------------------------------------------------------

    if result_ids is not None:

        if not isinstance(result_ids, list) or not result_ids:

            return JsonResponse({
                'success': False,
                'message': 'result_ids must be a non-empty list'
            }, status=400)

        ids = result_ids

    elif result_id is not None:

        ids = [result_id]

    else:

        logger.warning(
            "Manual movement failed: no result ID provided, user=%s",
            request.user.username
        )

        return JsonResponse({
            'success': False,
            'message': 'result_id or result_ids is required'
        }, status=400)

    # --------------------------------------------------------
    # UPDATE RESULTS
    # --------------------------------------------------------

    try:

        with transaction.atomic():

            results = ReconciliationResult.objects.filter(
                id__in=ids
            )

            found_ids = set(
                results.values_list('id', flat=True)
            )

            missing_ids = [
                result_id
                for result_id in ids
                if result_id not in found_ids
            ]

            if missing_ids:

                logger.warning(
                    "Manual movement failed: result IDs not found=%s, user=%s",
                    missing_ids,
                    request.user.username
                )

                return JsonResponse({
                    'success': False,
                    'message': 'Some reconciliation result IDs were not found',
                    'missing_ids': missing_ids
                }, status=404)

            movement_details = []

            for result in results:

                old_status = result.current_status

                result.current_status = new_status
                result.manual_status = True
                result.changed_by = request.user.username

                result.save()

                movement_details.append({
                    'result_id': result.id,
                    'old_status': old_status,
                    'new_status': result.current_status,
                    'original_status': result.original_status
                })

                logger.info(
                    "Manual reconciliation movement: "
                    "user=%s, result_id=%s, old_status=%s, "
                    "new_status=%s, original_status=%s",
                    request.user.username,
                    result.id,
                    old_status,
                    result.current_status,
                    result.original_status
                )

        # ----------------------------------------------------
        # FINAL LOG
        # ----------------------------------------------------

        logger.info(
            "Manual reconciliation movement completed: "
            "user=%s, moved_count=%s, new_status=%s",
            request.user.username,
            len(movement_details),
            new_status
        )

        return JsonResponse({
            'success': True,
            'message': 'Reconciliation result(s) moved successfully',
            'moved_count': len(movement_details),
            'result_ids': ids,
            'new_status': new_status,
            'changed_by': request.user.username,
            'results': movement_details
        }, status=200)

    except Exception:

        logger.exception(
            "Manual reconciliation movement failed unexpectedly: "
            "user=%s, result_ids=%s, new_status=%s",
            request.user.username,
            ids,
            new_status
        )

        return JsonResponse({
            'success': False,
            'message': 'Unable to move reconciliation results'
        }, status=500)
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='batch_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Batch ID for which the reconciliation results should be exported.'
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Optional filter by reconciliation status.'
        ),
        OpenApiParameter(
            name='gstin',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Optional filter by GSTIN.'
        ),
        OpenApiParameter(
            name='invoice_number',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Optional filter by invoice number.'
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Excel file exported successfully'
        ),
        400: OpenApiResponse(
            description='Missing or invalid parameters'
        ),
        404: OpenApiResponse(
            description='Batch not found or no reconciliation results found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        405: OpenApiResponse(
            description='Only GET method is allowed'
        ),
    },
    description='Export reconciliation results to an Excel file with optional filters.'
)

@api_view(['GET'])
@login_required
def export_reconciliation(request):
    logger.info(
        "Export request started: user=%s",
        request.user.username
    )

    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': 'Only GET method is allowed'
        }, status=405)

    batch_id = request.GET.get('batch_id')
    status = request.GET.get('status')
    gstin = request.GET.get('gstin')
    invoice_number = request.GET.get('invoice_number')
    logger.info(
        "Export request parameters: user=%s, batch_id=%s, status=%s, gstin=%s, invoice_number=%s",
        request.user.username,
        batch_id,
        status,
        gstin,
        invoice_number
    )

    if not batch_id:
        logger.warning(
            "Export request failed: batch_id missing, user=%s",
            request.user.username
        )
        return JsonResponse({
            'success': False,
            'message': 'batch_id is required'
        }, status=400)

    try:
        batch = UploadBatch.objects.get(
            batch_id=batch_id
        )
        logger.info(
            "Export batch found: batch_id=%s, current_status=%s",
            batch.batch_id,
            batch.status
        )
    except UploadBatch.DoesNotExist:
        logger.warning(
            "Export request failed: batch not found, user=%s, batch_id=%s",
            request.user.username,
            batch_id
        )
        return JsonResponse({
            'success': False,
            'message': 'Batch not found'
        }, status=404)

    queryset = ReconciliationResult.objects.filter(
        batch=batch
    ).order_by('id')

    if status:

        queryset = queryset.filter(
            current_status=status
        )

    if gstin:

        queryset = queryset.filter(
            gstin__icontains=gstin
        )

    if invoice_number:

        queryset = queryset.filter(
            invoice_number__icontains=invoice_number
        )

    results = list(queryset)
    logger.info(
        "Export records fetched: user=%s, batch_id=%s, total_records=%s, status=%s, gstin=%s, invoice_number=%s",
        request.user.username,
        batch_id,
        len(results),
        status,
        gstin,
        invoice_number
    )

    if not results:
        logger.warning(
            "Export request failed: no reconciliation results found, user=%s, batch_id=%s, status=%s, gstin=%s, invoice_number=%s",
            request.user.username,
            batch_id,
            status,
            gstin,
            invoice_number
        )
        return JsonResponse({
            'success': False,
            'message': 'No reconciliation results found'
        }, status=404)

    excel_file = export_results_to_excel(
        results
    )
    logger.info(
        "Excel export generated: user=%s, batch_id=%s, records=%s",
        request.user.username,
        batch_id,
        len(results)
    )

    filename_parts = [
        batch_id
    ]

    if status:

        filename_parts.append(
            status.replace(
                " ",
                "_"
            )
        )

    if gstin:

        filename_parts.append(
            f'GSTIN_{gstin}'
        )

    if invoice_number:

        filename_parts.append(
            f'Invoice_{invoice_number.replace("/", "_")}'
        )

    filename = (
        "_".join(filename_parts)
        + ".xlsx"
    )

    response = HttpResponse(
        excel_file.getvalue(),
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )
    logger.info(
        "Export completed successfully: user=%s, batch_id=%s, exported_records=%s, filename=%s",
        request.user.username,
        batch_id,
        len(results),
        filename
    )
    return response

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='batch_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Batch ID for which reconciliation summary is required.'
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Reconciliation summary returned successfully'
        ),
        400: OpenApiResponse(
            description='Batch ID is required'
        ),
        404: OpenApiResponse(
            description='Batch not found'
        ),
        401: OpenApiResponse(
            description='Authentication required'
        ),
        405: OpenApiResponse(
            description='Only GET method is allowed'
        ),
    },
    description='Get the bucket-wise reconciliation summary for a batch.'
)

@api_view(['GET'])
@login_required
def reconciliation_summary(request):

    logger.info(
        "Summary request started: user=%s",
        request.user.username
    )

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                'success': False,
                'message': 'Authentication required'
            },
            status=401
        )

    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': 'Only GET method is allowed'
        }, status=405)

    batch_id = request.GET.get('batch_id')
    logger.info(
        "Summary request parameters: user=%s, batch_id=%s",
        request.user.username,
        batch_id
    )

    if not batch_id:
        logger.warning(
            "Summary request failed: batch_id missing, user=%s",
            request.user.username
        )
        return JsonResponse({
            'success': False,
            'message': 'batch_id is required'
        }, status=400)

    try:
        batch = UploadBatch.objects.get(batch_id=batch_id)
        logger.info(
            "Summary batch found: batch_id=%s, current_status=%s",
            batch.batch_id,
            batch.status
        )
    except UploadBatch.DoesNotExist:
        logger.warning(
            "Summary request failed: batch not found, user=%s, batch_id=%s",
            request.user.username,
            batch_id
        )
        return JsonResponse({
            'success': False,
            'message': 'Batch not found'
        }, status=404)

    results = ReconciliationResult.objects.filter(
        batch=batch
    )

    summary = {
        'Matched': 0,
        'Mismatch': 0,
        'Amount Mismatch': 0,
        '2B Only': 0,
        'Purchase Only': 0
    }

    for result in results:
        if result.current_status in summary:
            summary[result.current_status] += 1
    logger.info(
        "Summary calculated: user=%s, batch_id=%s, total_records=%s, summary=%s",
        request.user.username,
        batch_id,
        results.count(),
        summary
    )
    logger.info(
        "Summary request completed successfully: user=%s, batch_id=%s",
        request.user.username,
        batch_id
    )

    return JsonResponse({
        'success': True,
        'batch_id': batch.batch_id,
        'total_records': results.count(),
        'summary': summary
    }, status=200)