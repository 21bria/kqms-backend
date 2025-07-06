from django import forms
from django.contrib.auth.models import User, Group, Permission
from ..models import PermissionGroup, Menu

class PermissionGroupForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required=True,
        label="Groups"
    )

    class Meta:
        model    = PermissionGroup
        fields   = ['name', 'groups']
        widgets  = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Permission Group Name'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        group_id = self.instance.pk  # Mengambil ID grup yang sedang diedit
        # Jika ada grup lain dengan nama yang sama dan ID yang berbeda, tampilkan error
        if PermissionGroup.objects.filter(name=name).exclude(id=group_id).exists():
            raise forms.ValidationError('Permission Group with this Name already exists.')
        return name