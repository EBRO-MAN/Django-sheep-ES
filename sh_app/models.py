from django.db import models
from django.core.exceptions import ValidationError

class Sheep(models.Model):
    SEX_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    TYPE_CHOICES = [
        ('LAMB', 'Lamb'),
        ('YOUNG_RAM', 'Young Ram'),
        ('GIMMER', 'Gimmer'),
        ('RAM', 'Ram'),
        ('EWE', 'Ewe'),
    ]
    
    BREED_CHOICES = [
        ('LOCAL', 'Local'),
        ('PA', 'PA'),
        ('PD', 'PD'),
        ('AC', 'AC'),
        ('DC', 'DC'),
    ]
    
    ear_tag_number = models.CharField(max_length=50, unique=True, primary_key=True)
    breed = models.CharField(max_length=10, choices=BREED_CHOICES)
    breed_level = models.FloatField()
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    birth_weight = models.FloatField(null=True, blank=True)
    separation_date = models.DateField(null=True, blank=True)
    separation_weight = models.FloatField(null=True, blank=True)
    parent_ewe = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ewe_offspring',
        limit_choices_to={'sex': 'FEMALE'}
    )
    parent_ram = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ram_offspring',
        limit_choices_to={'sex': 'MALE'}
    )
    is_healthy = models.BooleanField(default=True)
    health_notes = models.TextField(blank=True)
    flagged_for_culling = models.BooleanField(default=False)
    culling_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # Validate parent relationships
        if self.parent_ewe and self.parent_ewe.sex != 'FEMALE':
            raise ValidationError("Parent ewe must be female")
        if self.parent_ram and self.parent_ram.sex != 'MALE':
            raise ValidationError("Parent ram must be male")
        
        # Auto-culling rule
        if self.separation_weight and self.separation_weight < 11:
            self.flagged_for_culling = True
            if not self.culling_reason:
                self.culling_reason = "Low Separation Weight"
    
    def __str__(self):
        return f"{self.ear_tag_number} - {self.breed} - {self.type}"
