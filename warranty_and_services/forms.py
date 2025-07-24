from django import forms
from .models import ServiceFormEntry

class ServiceFormEntryAdminForm(forms.ModelForm):
    """Admin form for ServiceFormEntry - simplified without file uploads"""
    class Meta:
        model = ServiceFormEntry
        fields = [
            'installation', 'service_followup', 'service_type', 'service_date', 'service_time',
            'checked_controls', 'changed_spare_parts', 'notes'
        ]
        widgets = {
            'service_type': forms.RadioSelect(),
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'service_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
