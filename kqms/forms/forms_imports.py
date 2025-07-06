from django import forms
from django.apps import apps


class ImportForm(forms.Form):
    excel_file = forms.FileField(label='Choose Excel File')
    start_cell = forms.CharField(max_length=5, label='Start Cell')
    end_cell = forms.CharField(max_length=5, label='End Cell')
    table_choice = forms.ChoiceField(
        choices=[(model._meta.label, model._meta.verbose_name) for model in apps.get_models()],
        label='Choose Table'
    )

    def __init__(self, *args, **kwargs):
        super(ImportForm, self).__init__(*args, **kwargs)
        self.fields['columns'] = forms.MultipleChoiceField(choices=[], label='Choose Columns')

    def set_column_choices(self, columns):
        self.fields['columns'].choices = [(col, col) for col in columns]

    def get_fields(self, model):
        return model._meta.fields if model else []
    
# forms.py

class ExcelUploadForm(forms.Form):
    file = forms.FileField()