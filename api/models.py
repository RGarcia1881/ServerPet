from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json 
from .managers import CustomUserManager

# --- Modelo User (Usuario Personalizado) ---
class User(AbstractBaseUser, PermissionsMixin):
    # Campos que necesitamos explícitamente:
    email = models.EmailField(unique=True, verbose_name='Email Address')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='usersImages/', null=True, blank=True)
    
    # Campos de AbstractUser que necesitamos redefinir para permisos
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager() 
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return self.email
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

# --- Modelo Pet ---
class Pet(models.Model):
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
    ubication = models.CharField(max_length=255)
    
    # 🔥 CAMBIO: status ahora es BooleanField
    status = models.BooleanField(default=True)  # True = Activo, False = Inactivo
    
    FC = models.IntegerField()  # Frecuencia de Comida
    WC = models.IntegerField()  # Peso de Comida
    
    # 🔥 CAMBIOS: FP y WP ahora son BooleanField
    FP = models.BooleanField(default=False)  # Frecuencia de Paseo (True = Habilitado, False = Deshabilitado)
    WP = models.BooleanField(default=False)  # Peso de Paseo (True = Habilitado, False = Deshabilitado)
    
    # 🔥 NUEVO ATRIBUTO: horarios como JSONField
    horarios = models.JSONField(default=list, blank=True)
    
    # Relaciones
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispensers')
    pet = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name='dispenser', null=True, blank=True)

    def __str__(self):
        return f"Dispensador en {self.ubication}"

# --- 🔥 NUEVO MODELO: Horarios ---
class Horario(models.Model):
    """
    Modelo para gestionar horarios específicos de dispensación por mascota.
    """
    mascota = models.ForeignKey(
        Pet, 
        on_delete=models.CASCADE, 
        related_name='horarios',
        verbose_name='Mascota'
    )
    
    dispensador = models.ForeignKey(
        Dispenser,
        on_delete=models.CASCADE,
        related_name='horarios_programados',
        verbose_name='Dispensador Asignado'
    )
    
    # 🔥 TEMPORAL: Permitir nulos para la migración
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='horarios_usuario',
        verbose_name='Usuario Propietario',
        null=True,
        blank=True
    )
    
    horarios = models.JSONField(
        default=list,
        help_text='Lista de horarios en formato ["08:00", "12:00", "19:00"]'
    )
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # 🔥 Asignar automáticamente el usuario de la mascota
        if not self.usuario and self.mascota:
            self.usuario = self.mascota.user
            
        # Si no se especifica un dispensador, usar el asignado a la mascota
        if not self.dispensador and self.mascota:
            try:
                self.dispensador = self.mascota.dispenser
            except Dispenser.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def __str__(self):
        usuario_email = self.usuario.email if self.usuario else "Sin usuario"
        return f"Horarios de {self.mascota.name} - Usuario: {usuario_email}"
    
    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        unique_together = ['mascota', 'dispensador']


# --- 🔥 SEÑALES PARA SINCRONIZACIÓN AUTOMÁTICA ---

@receiver(post_save, sender=Horario)
def actualizar_horarios_dispensador(sender, instance, **kwargs):
    """
    Actualiza automáticamente el campo 'horarios' del dispensador
    cuando se guarda un registro en Horario.
    """
    dispensador = instance.dispensador
    
    # Obtener todos los horarios únicos de este dispensador
    todos_horarios = set()
    
    # Recorrer todos los registros de Horario para este dispensador
    horarios_del_dispensador = Horario.objects.filter(dispensador=dispensador)
    
    for horario_reg in horarios_del_dispensador:
        for hora in horario_reg.horarios:
            todos_horarios.add(hora)
    
    # Convertir a lista ordenada
    horarios_ordenados = sorted(list(todos_horarios))
    
    # Actualizar el dispensador
    dispensador.horarios = horarios_ordenados
    dispensador.save(update_fields=['horarios'])
    
    print(f"✅ Horarios actualizados para dispensador {dispensador.id}: {horarios_ordenados}")


@receiver(post_delete, sender=Horario)
def actualizar_horarios_dispensador_eliminado(sender, instance, **kwargs):
    """
    Actualiza automáticamente el campo 'horarios' del dispensador
    cuando se elimina un registro en Horario.
    """
    dispensador = instance.dispensador
    
    # Obtener todos los horarios únicos restantes de este dispensador
    todos_horarios = set()
    
    horarios_del_dispensador = Horario.objects.filter(dispensador=dispensador)
    
    for horario_reg in horarios_del_dispensador:
        for hora in horario_reg.horarios:
            todos_horarios.add(hora)
    
    # Convertir a lista ordenada
    horarios_ordenados = sorted(list(todos_horarios))
    
    # Actualizar el dispensador
    dispensador.horarios = horarios_ordenados
    dispensador.save(update_fields=['horarios'])
    
    print(f"✅ Horarios actualizados (post-delete) para dispensador {dispensador.id}: {horarios_ordenados}")


# --- 🔥 SEÑAL PARA CUANDO SE ACTUALIZA UNA MASCOTA ---
@receiver(post_save, sender=Pet)
def asignar_dispensador_automatico(sender, instance, **kwargs):
    """
    Si una mascota tiene un dispensador asignado, crear automáticamente
    un registro de Horario para ella.
    """
    try:
        dispensador = instance.dispenser
        # Verificar si ya existe un horario para esta mascota y dispensador
        if not Horario.objects.filter(mascota=instance, dispensador=dispensador).exists():
            Horario.objects.create(
                mascota=instance,
                dispensador=dispensador,
                usuario=instance.user,
                horarios=["08:00", "18:00"]  # Horarios por defecto
            )
            print(f"✅ Horario creado automáticamente para {instance.name}")
    except Dispenser.DoesNotExist:
        # La mascota no tiene dispensador asignado
        pass