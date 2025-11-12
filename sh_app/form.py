from django import forms
from .models import Sheep

# Create Add Sheep Record
class AddRecordForm(forms.ModelForm):
    ear_tag_number = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Ear tag", "class": "form-control"}), label="")
    breed = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Breed", "class": "form-control"}), label="")
    breed_level =forms.FloatField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Breed level", "class": "form-control"}), label="")
    sex = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Sex", "class": "form-control"}), label="")
    type = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Type", "class": "form-control"}), label="")
    date_of_birth = forms.DateField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Date of birth", "class": "form-control"}), label="")
    birth_weight =forms.FloatField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Birth weight", "class": "form-control"}), label="")
    separation_date = forms.DateField( widget=forms.widgets.TextInput(attrs={"placeholder": "Separation date", "class": "form-control"}), label="")
    separation_weight = forms.FloatField( widget=forms.widgets.TextInput(attrs={"placeholder": "Separation weight", "class": "form-control"}), label="")
    # parent_ewe = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Parent ewe", "class": "form-control"}), label="")
    # parent_ram = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Parent ram", "class": "form-control"}), label="")
    # is_healthy =forms.BooleanField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Health status", "class": "form-control"}), label="")
    # health_notes = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Health note", "class": "form-control"}), label="")
    # flagged_for_culling = forms.BooleanField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Flag for culling", "class": "form-control"}), label="")
    # culling_reason = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Culling reason", "class": "form-control"}), label="")

    class Meta:
        model = Sheep
        exclude = ("user",)