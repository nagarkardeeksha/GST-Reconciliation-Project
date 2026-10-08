from django.contrib import admin
from .models import UploadBatch, MasterConfiguration


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_id',
        'reconciliation_month',
        'status',
        'uploaded_at'
    )


@admin.register(MasterConfiguration)
class MasterConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_active',
        'created_at',
        'updated_at'
    )               