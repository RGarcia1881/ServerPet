from pathlib import Path
from datetime import timedelta # Necesario para la configuración de SIMPLE_JWT

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-bqo=2x*nf$6poo6wfx1=-x38a#@!sijmuep5q6el984ur59!f#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones de terceros
    'rest_framework',
    'corsheaders',
    'drf_spectacular',  # For API documentation
    'rest_framework_simplejwt',
    
    # Aplicaciones locales
    'api',
]

# Indicar a Django que use su modelo de usuario personalizado
AUTH_USER_MODEL = 'api.User' 

# Configuración de Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Tiempo de validez del Access Token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),   # Tiempo de validez del Refresh Token
    "ROTATE_REFRESH_TOKENS": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "USER_ID_FIELD": "id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
}

# === Configuración de REST_FRAMEWORK (ÚNICA DEFINICIÓN) ===
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Aseguramos que todas las vistas requieran JWT por defecto
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Corrección: Quité el segundo diccionario duplicado de REST_FRAMEWORK
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

# === DESHABILITACIÓN TOTAL DE VALIDACIÓN DE CONTRASEÑA ===
# Esto permite usar contraseñas simples o cortas en el Admin.
AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static and Media Files (CRÍTICO para imágenes)
# -----------------------------------------------
STATIC_URL = 'static/'
# Directorio donde Django buscará archivos estáticos
STATICFILES_DIRS = [BASE_DIR / "static"] 
# Directorio donde se recolectarán los archivos estáticos para producción
STATIC_ROOT = BASE_DIR / "staticfiles"

# Directorios de Archivos Media (Imágenes subidas por el usuario)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# -----------------------------------------------


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Dispensador de Mascotas',
    'DESCRIPTION': 'API REST para controlar dispensadores y gestionar usuarios y mascotas.',
    'VERSION': '1.0.0',
    'CONTACT': {
        'name': 'Raúl García',
        'email': 'rgb101001@gmail.com',
        'url': 'https://rb-code-studio.vercel.app/',
    },
    'SERVE_INCLUDE_SCHEMA': False, # Mejor dejar la ruta /schema/ separada
}

# === Configuración para deshabilitar la validación de email en formularios de Django ===
# Si necesitas un validador de email más relajado:
from django.core.validators import EmailValidator
EmailValidator.regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"