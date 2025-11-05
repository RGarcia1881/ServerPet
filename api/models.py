from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
import json 
from .managers import CustomUserManager # Importamos el manager personalizado

# --- Modelo User (Usuario Personalizado) ---
# Heredamos de AbstractBaseUser (para autenticación) y PermissionsMixin (para permisos)
class User(AbstractBaseUser, PermissionsMixin):
    # Campos que necesitamos explícitamente:
    email = models.EmailField(unique=True, verbose_name='Email Address')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='usersImages/', null=True, blank=True)
    
    # Campos de AbstractUser que necesitamos redefinir para permisos
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True) # Mantenemos para registro de creación

    # Usamos nuestro manager personalizado
    objects = CustomUserManager() 
    
    # Indicamos a Django que use el email como campo de inicio de sesión
    USERNAME_FIELD = 'email'
    
    # Campos que se piden al usar createsuperuser (ya no se pide 'username')
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return self.email
        
    # Métodos necesarios para compatibilidad con AbstractUser/Admin
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

# --- Modelo Pet ---
class Pet(models.Model):
# ... (Código Pet sin cambios)
    name = models.CharField(max_length=100)
    race = models.CharField(max_length=100)
    weight = models.FloatField()
    age = models.IntegerField()
    image = models.ImageField(upload_to='petsImages/', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')

    def __str__(self):
        return self.name

# --- Modelo Dispenser ---
class Dispenser(models.Model):
# ... (Código Dispenser sin cambios)
    ubication = models.CharField(max_length=255)
    status = models.CharField(max_length=50) # Ejemplo: 'Activo', 'Inactivo'
    FC = models.IntegerField() # Frecuencia de Comida
    WC = models.IntegerField() # Peso de Comida
    FP = models.IntegerField() # Frecuencia de Paseo
    WP = models.IntegerField() # Peso de Paseo
    
    # Relaciones
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispensers')
    pet = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name='dispenser', null=True, blank=True) # Un dispensador por mascota

    def __str__(self):
        return f"Dispensador en {self.ubication}"