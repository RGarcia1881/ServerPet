# api/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Horario, Pet, Dispenser

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
                horarios=["08:00", "18:00"]  # Horarios por defecto
            )
            print(f"✅ Horario creado automáticamente para {instance.name}")
    except Dispenser.DoesNotExist:
        # La mascota no tiene dispensador asignado
        pass