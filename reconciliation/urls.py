from django.urls import path
from .views import (
    test_api,
    login_api,
    upload_excel,
    master_configuration_api,
    start_reconciliation,
    reconciliation_results,
    move_reconciliation,
    export_reconciliation,
)

urlpatterns = [
    path('test/', test_api, name='test_api'),
    path('login/', login_api, name='login_api'),
    path('upload/', upload_excel, name='upload_excel'),
    path('master/', master_configuration_api, name='master_configuration_api'),

    path('reconciliation/start/', start_reconciliation, name='start_reconciliation'),
    path('reconciliation/results/', reconciliation_results, name='reconciliation_results'),
    path('reconciliation/move/', move_reconciliation, name='move_reconciliation'),
    path('reconciliation/export/', export_reconciliation, name='export_reconciliation'),
]