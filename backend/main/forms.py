from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import TickerItem

class TickerItemForm(forms.ModelForm):
    class Meta:
        model = TickerItem
        fields = ['ticker', 'content', 'order','is_active']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, config_name="comment"
            )
        }