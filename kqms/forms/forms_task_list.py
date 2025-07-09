from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.utils.module_loading import import_string
from ..models import TaskList

class TaskListForm(forms.ModelForm):
    allowed_group_names_field = forms.MultipleChoiceField(
        choices=[(g.name, g.name) for g in Group.objects.all()],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required=False,
        label="Allowed Groups"
    )

    class Meta:
        model = TaskList
        fields = ['type_table', 'task_path', 'status']  # tidak masukkan allowed_group_names langsung
        widgets = {
            'type_table': forms.TextInput(attrs={
                'class': 'form-control flex-1',
                'placeholder': 'Enter table',
                'required': True
            }),
            'task_path': forms.TextInput(attrs={
                'class': 'form-control flex-1',
                'placeholder': 'kqms.task.path_file.class',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.allowed_group_names:
            self.fields['allowed_group_names_field'].initial = self.instance.allowed_group_names

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.allowed_group_names = self.cleaned_data.get('allowed_group_names_field', [])
        if commit:
            instance.save()
        return instance

    def clean_task_path(self):
        task_path = self.cleaned_data.get('task_path')

        if not task_path:
            raise ValidationError("Task path tidak boleh kosong.")

        try:
            import_string(task_path)
        except Exception as e:
            raise ValidationError(f"Task path tidak valid: {str(e)}")

        return task_path

    def clean(self):
        cleaned_data = super().clean()
        type_table = cleaned_data.get('type_table')
        task_path = cleaned_data.get('task_path')

        if not type_table:
            self.add_error('type_table', "Type Table tidak boleh kosong.")

        existing_type = TaskList.objects.filter(type_table=type_table).exclude(id=self.instance.id).first()
        if existing_type:
            self.add_error('type_table', "Type Table sudah ada.")

        if task_path:
            existing_path = TaskList.objects.filter(task_path=task_path).exclude(id=self.instance.id).first()
            if existing_path:
                self.add_error('task_path', "Task Path sudah terdaftar di data lain.")

        return cleaned_data
