from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

#User model
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Puedes usar hashing después

    def __str__(self):
        return self.name

#Pet model    
class Pet(models.Model):
    name = models.CharField(max_length=100)
    weight = models.FloatField()
    age = models.PositiveIntegerField()
    race = models.CharField(max_length=100)
    image = models.ImageField(upload_to='pets/', null=True, blank=True)  # ← Campo nuevo
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='pets')

    def __str__(self):
        return f"{self.name} ({self.race})"


#Dispenser model
class Dispenser(models.Model):
    ubication = models.CharField(max_length=100)
    status = models.BooleanField(default=False)
    timetable = models.CharField(max_length=255)

    # Componentes físicos
    FC = models.FloatField()  # Food Container
    WC = models.FloatField()  # Water Container
    FP = models.BooleanField(default=False)  # Food Plate
    WP = models.BooleanField(default=False)  # Water Plate

    # Relaciones
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispensers')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='dispensers')

    def __str__(self):
        return f"Dispenser at {self.ubication} for {self.pet.name}"