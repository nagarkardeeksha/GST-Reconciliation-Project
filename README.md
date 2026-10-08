# GST Reconciliation Application

A Django-based application for reconciling GSTR-2B data with Purchase data.

## Project Overview

The application allows users to:

- Login to the application
- Upload GSTR-2B and Purchase Excel files
- Validate uploaded files
- Store Excel data in SQL Server
- Reconcile 2B data with Purchase data
- View reconciliation results
- Manually change reconciliation status
- Export reconciliation results

## Technologies Used

- Python
- Django
- Django REST Framework
- SQL Server
- Pandas
- OpenPyXL
- pyodbc
- mssql-django
- drf-spectacular

## Application Flow

Login
↓
Upload 2B & Purchase Excel Files
↓
Validate Files
↓
Store Data in Database
↓
Start Reconciliation
↓
Generate Results
↓
Review / Change Status
↓
Export Results

## APIs

| Method | API | Purpose |
|---|---|---|
| POST | `/api/login/` | User login |
| POST | `/api/upload/` | Upload 2B and Purchase files |
| GET/POST | `/api/master/` | Manage reconciliation configuration |
| POST | `/api/reconciliation/start/` | Start reconciliation |
| GET | `/api/reconciliation/results/` | Get reconciliation results |
| GET | `/api/reconciliation/summary/` | Get reconciliation summary |
| POST | `/api/reconciliation/move/` | Change reconciliation status |
| GET | `/api/reconciliation/export/` | Export results |

## Database

The application uses SQL Server.

Main tables:

- `UploadBatch` – Stores uploaded batch and file information
- `TwoBData` – Stores GSTR-2B Excel data
- `PurchaseData` – Stores Purchase Excel data
- `ReconciliationResult` – Stores reconciliation results
- `MasterConfiguration` – Stores reconciliation configuration

## Reconciliation Buckets

The application categorizes records into:

- Matched
- Mismatch
- Amount Mismatch
- 2B Only
- Purchase Only

## Project Structure

```text
gst_reconciliation_main/
│
├── gst_reconciliation/
├── reconciliation/
├── input_file/
├── logs/
├── media/
├── manage.py
├── index.html
├── requirements.txt
└── README.md
