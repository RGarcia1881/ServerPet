from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Importamos ModelForm, que es más flexible que UserCreationForm para AbstractBaseUser
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User, Pet, Dispenser, Horario

# Paso 1: Crear un formulario de adición basado en Email usando ModelForm
class UserAdminCreationForm(forms.ModelForm):
    """
    Formulario personalizado para crear usuarios. 
    Usamos ModelForm y añadimos los campos de contraseña manualmente.
    """
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)

    class Meta:
        model = User
        # CRÍTICO: Usamos 'exclude' para asegurar que no se incluyan campos 
        # gestionados automáticamente por Django o de seguridad, como 'date_joined'.
        # Solo manejamos los campos que el usuario DEBE llenar.
        exclude = (
            'date_joined', 
            'last_login', 
            'is_superuser', 
            'is_staff', 
            'groups', 
            'user_permissions'
        )
        
    def clean_password2(self):
        # Verificamos que las contraseñas coincidan.
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."),
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        """Sobrescribimos save para usar el manager de nuestro modelo y setear la contraseña."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Aseguramos que el nuevo usuario sea activo por defecto, si el campo no se maneja
        if 'is_active' not in self.cleaned_data:
            user.is_active = True
        
        if commit:
            user.save()
        return user


# Paso 2: Registrar el modelo User con el administrador personalizado
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Usamos nuestro formulario de creación personalizado
    add_form = UserAdminCreationForm 
    
    # Definimos campos de solo lectura para la vista de EDICIÓN.
    readonly_fields = ('last_login', 'date_joined') 
    
    # list_display usa 'email' como identificador principal
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'image') 
    
    # Definición de los campos a mostrar al editar un usuario
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # La autenticación se basa en email
        ('Información Personal', {'fields': ('first_name', 'last_name', 'image')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        # Fechas, ahora como solo lectura
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    # === Formulario de Adición (USA LA CLASE UserAdminCreationForm) ===
    # add_fieldsets define el layout de los campos definidos en add_form.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Incluimos los campos necesarios para la creación
            'fields': ('email', 'first_name', 'last_name', 'image', 'password', 'password2'), 
        }),
    )
    
    # Campos que el usuario puede buscar
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Grupos y Permisos
    filter_horizontal = ('groups', 'user_permissions',) 

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'race', 'weight', 'age', 'user', 'image')
    list_filter = ('race', 'age', 'user')
    # CRÍTICO: Búsqueda por user__email
    search_fields = ('name', 'race', 'user__email') 
    ordering = ('id',)

@admin.register(Dispenser)
class DispenserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ubication',
        'status',
        'FC',
        'WC',
        'FP',
        'WP',
        'user',
        'pet'
    )
    list_filter = ('status', 'FP', 'WP', 'user', 'pet')
    # CRÍTICO: Búsqueda por user__email
    search_fields = ('ubication', 'user__email', 'pet__name') 
    ordering = ('id',)

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ['mascota', 'dispensador', 'horarios_display', 'creado_en']
    list_filter = ['dispensador', 'mascota__user']
    search_fields = ['mascota__name', 'dispensador__ubication']
    
    def horarios_display(self, obj):
        return ", ".join(obj.horarios) if obj.horarios else "Sin horarios"
    horarios_display.short_description = 'Horarios'