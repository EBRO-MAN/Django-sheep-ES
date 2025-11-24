from django import forms
from .models import Sheep

# Create Add Sheep Record
class AddRecordForm(forms.ModelForm):
    ear_tag_number = forms.CharField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Ear tag", "class": "form-control"}), label="Ear Tag Number")
    # breed = forms.ChoiceField(required=True, widget=forms.widgets.Select(attrs={"placeholder": "Breed", "class": "form-control"}), label="")
    breed = forms.ChoiceField(choices=Sheep.BREED_CHOICES, widget=forms.Select(attrs={"class": "form-control"}), label="Breed")
    breed_level =forms.FloatField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Breed level", "class": "form-control"}), label="Breed Level (%)")
    sex = forms.ChoiceField(choices=Sheep.SEX_CHOICES, widget=forms.Select(attrs={"class": "form-control"}), label="Sex")
    type = forms.ChoiceField(choices=Sheep.TYPE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}), label="Sheep Type")
    # date_of_birth = forms.DateField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Date of birth", "class": "form-control"}), label="")
    # date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}), label="Date of Birth")
    date_of_birth = forms.DateField(
    label="Date of Birth",
    required=False,
    widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
        "placeholder": "mm/dd/yyyy"
    })
)

    birth_weight =forms.FloatField(required=True, widget=forms.widgets.TextInput(attrs={"placeholder": "Birth weight", "class": "form-control"}), label="Birth Weight (kg)")
    # separation_date = forms.DateField( widget=forms.widgets.TextInput(attrs={"placeholder": "Separation date", "class": "form-control"}), label="")
    # separation_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}), label="Separation Date")
    separation_date = forms.DateField(
    label="Separation Date",
    required=False,
    widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control",
        "placeholder": "mm/dd/yyyy"
    })
)

    # separation_weight = forms.FloatField( widget=forms.widgets.TextInput(attrs={"placeholder": "Separation weight", "class": "form-control"}), label="Separation Weight (kg)")
    separation_weight = forms.FloatField(
    label="Separation Weight (kg)",
    required=False,
    widget=forms.NumberInput(attrs={"placeholder": "Separation weight", "class": "form-control"})
)

    # parent_ewe = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Parent ewe", "class": "form-control"}), label="")
    parent_ewe = forms.ModelChoiceField(
    queryset=Sheep.objects.filter(type='EWE'),
    required=False,
    widget=forms.Select(attrs={"class": "form-control"}),
    label="Parent Ewe (Mother)"
)

    # parent_ram = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Parent ram", "class": "form-control"}), label="")
    parent_ram = forms.ModelChoiceField(
    queryset=Sheep.objects.filter(type='RAM'),
    required=False,
    widget=forms.Select(attrs={"class": "form-control"}),
    label="Parent Ram (Father)"
)

    # is_healthy = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), label="Is Healthy")
    is_healthy = forms.BooleanField(
    label="Is the Sheep Healthy?",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
)


    health_notes = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Health note", "class": "form-control"}), label="Health Notes")
    state = forms.ChoiceField(choices=Sheep.STATE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}), label="Sheep State")
    # flagged_for_culling = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}), label="Flagged for Culling")
    flagged_for_culling = forms.BooleanField(
    label="Flag for Culling?",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
)


    culling_reason = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={"placeholder": "Culling reason", "class": "form-control"}), label="Culling Reason")

    class Meta:
        model = Sheep
        exclude = ("user",)


# breeding/forms.py

from .models import BreedingCycle

class RamSelectionForm(forms.Form):
    rams = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        label="Select Rams for Breeding"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .services import get_available_rams
        self.fields['rams'].queryset = get_available_rams()

class BreedingAssignmentForm(forms.Form):
    """Form for final breeding assignments"""
    def __init__(self, *args, **kwargs):
        ram_ewe_assignments = kwargs.pop('ram_ewe_assignments', {})
        super().__init__(*args, **kwargs)
        
        for ram_id, ewe_list in ram_ewe_assignments.items():
            for ewe in ewe_list:
                field_name = f"assign_{ram_id}_{ewe.ear_tag_number}"
                self.fields[field_name] = forms.BooleanField(
                    initial=True,
                    required=False,
                    label=f"{ewe.ear_tag_number} - {ewe.breed}"
                )