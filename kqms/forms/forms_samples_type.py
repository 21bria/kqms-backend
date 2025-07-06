from django import forms
from django.apps import apps
from ..models.sample_type import SampleType
from ..models.sample_type_details import SampleTypeDetails


class SampleTypeForm(forms.ModelForm):
    class Meta:
        model = SampleType
        fields = ['id','type_sample', 'keterangan', 'status']
    
    # def clean_type_sample(self):
    #     type_sample = self.cleaned_data['type_sample']
    #     if SampleType.objects.filter(type_sample=type_sample).exists():
    #         raise forms.ValidationError("Type sample already exists.")
    #     return type_sample
    def clean_type_sample(self):
        type_sample = self.cleaned_data.get('type_sample')

        if not type_sample:
            return type_sample  # Biarkan validator bawaan menangani jika kosong

        # Cek apakah ada type_sample lain dengan nama yang sama
        qs = SampleType.objects.filter(type_sample=type_sample)

        # Kecualikan dirinya sendiri saat update
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Type sample already exists.")

        return type_sample



class SampleTypeDetailsForm(forms.ModelForm):
    class Meta:
        model  = SampleTypeDetails
        fields = ['id_method']

