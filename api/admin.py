from django.contrib import admin
from .models import User, Pet, Dispenser

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'password')

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'race', 'weight', 'age', 'user', 'image')

@admin.register(Dispenser)
class DispenserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ubication',
        'status',
        'timetable',
        'FC',
        'WC',
        'FP',
        'WP',
        'user',
        'pet'
    )
