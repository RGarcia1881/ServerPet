from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Manager de usuario personalizado donde el email es el identificador único.
    Basado en AbstractBaseUser, solo maneja el email y password.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un User con el email y password dados.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Inyectar valores por defecto para los campos opcionales (first_name, last_name)
        extra_fields.setdefault('first_name', '')
        extra_fields.setdefault('last_name', '')
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un Superuser con el email y password dados.
        """
        # Campos mínimos para superusuario
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        # Inyectar valores por defecto que se piden en REQUIRED_FIELDS
        extra_fields.setdefault('first_name', 'Admin')
        extra_fields.setdefault('last_name', 'User')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)