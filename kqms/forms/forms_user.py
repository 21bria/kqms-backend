from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.conf import settings

class CustomUserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset = Group.objects.all(),
        widget   = forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required = False,
        label    = "Groups"
    )
    
    user_permissions = forms.ModelMultipleChoiceField(
        queryset = Permission.objects.all(),
        widget   = forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),
        required = False,
        label    = "Permissions"
    )


    class Meta:
        model   = User
        fields  = ['username', 'first_name','last_name','email', 'is_staff', 'is_active', 'groups', 'user_permissions']
        widgets = {
            'username'   : forms.TextInput(attrs={'class': 'form-control flex-1', 'placeholder': 'Enter Username'}),
            'first_name' : forms.TextInput(attrs={'class': 'form-control flex-1', 'placeholder': 'Enter First Name'}),
            'last_name'  : forms.TextInput(attrs={'class': 'form-control flex-1', 'placeholder': 'Enter Last Name'}),
            'email'      : forms.EmailInput(attrs={'class': 'form-control flex-1', 'placeholder': 'Enter Email'}),
            'is_staff'   : forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active'  : forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        error_messages = {
            'username': {
                'max_length': "Username must be 150 characters or fewer.",
                'invalid'   : "Enter a valid username. Only letters, digits, and @/./+/-/_ are allowed.",
            },
        }

class CustomGroupForm(forms.ModelForm):
    permissions  = forms.ModelMultipleChoiceField(
        queryset = Permission.objects.all(),
        # widget   = forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox'}),  # Tambahkan class CSS
        widget   = forms.CheckboxSelectMultiple,
        required = False,
        label    = "Permissions"
    )

    def clean(self):
        cleaned_data = super().clean()

        # Cegah error INSERT dengan ID duplikat
        if not self.instance.pk and 'id' in self.data:
            self.instance.pk = None  # Abaikan id jika sedang create

        return cleaned_data

    
    class Meta:
        model   = Group
        fields  = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control flex-1', 'placeholder': 'Enter Group Name'}),  # Tambahkan style di field name
        }
