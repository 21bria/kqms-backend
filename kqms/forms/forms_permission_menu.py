from django import forms
from ..models import Menu, PermissionGroup

class MenuForm(forms.ModelForm):
    permission = forms.ModelChoiceField(
        queryset=PermissionGroup.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Permission Group"
    )
    parent = forms.ModelChoiceField(
        queryset=Menu.objects.filter(parent=None),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Parent Menu"
    )

    class Meta:
        model = Menu
        fields = ['name', 'url', 'permission', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter Menu Name'}),
            'url': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter URL'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
