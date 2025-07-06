
from pathlib import Path
import os
from django.templatetags.static import static
from tzlocal import get_localzone_name
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o7bfi@8g*6@^x0^=8^0pk8(&3ili&u@u&eb*@(_7m2)a!j3xbu'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'mozilla_django_oidc',
    'django.contrib.gis',
    'django_celery_beat',
    'accounts',
    'kqms',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # WAJIB DI ATAS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'kqms.context_processors.sidebar_menu', #untuk menu dinamis
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.postgresql',
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # ← HARUS INI
        # 'NAME': 'main_db',
        'NAME': 'kqms_db',
        'USER': 'postgres',
        'PASSWORD': '211989',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'kqms_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kqms_db',
        'USER': 'postgres',
        'PASSWORD': '211989',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    # 'ksafe_db': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'db_ksafe',
    #     'USER': 'postgres',
    #     'PASSWORD': '211989',
    #     'HOST': 'localhost',
    #     'PORT': '5432',
    # }
}


# DATABASE_ROUTERS = [
#     'routers.db_routers.KQMSRouter',
#     'routers.db_routers.KSafeRouter',
#     'routers.db_routers.AuthRouter',
# ]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    'accounts.auth_backends.MyOIDCBackend',
    'accounts.auth_backends.GoogleOIDCBackend',
    'accounts.auth_backends.MicrosoftOIDCBackend',
     'kqms.authentication.EmailBackend',                  # Ganti sesuai app kamu
    'django.contrib.auth.backends.ModelBackend',
]


ORS_ALLOW_CREDENTIALS = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False  # kalau masih localhost
# (Opsional) Kalau pakai credentials (cookie, token via fetch):
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = ['*']

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Nuxt dev server
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}


LOGIN_URL = '/oidc/authenticate/'
LOGIN_REDIRECT_URL = '/api/accounts/oidc/redirect/'


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
# TIME_ZONE = str(get_localzone())  # misalnya 'Asia/Makassar'
try:
    TIME_ZONE = get_localzone_name()  # Misalnya: 'Asia/Makassar'
except Exception:
    TIME_ZONE = 'Asia/Jakarta'  # fallback default

USE_TZ = True

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
# Jika ingin menambahkan folder static tambahan
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static/'),
]

# Jika ingin menyimpan static files hasil collect static di folder tertentu
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Celery 

#setup redis on local machine 
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

CELERY_TASK_SOFT_TIME_LIMIT = 300      # 5 menit
CELERY_TASK_TIME_LIMIT = 600           # 10 menit (paksa terminate)
CELERY_TASK_RESULT_EXPIRES = 3600      # Hasil task hilang dalam 1 jam

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 43200        # 12 jam, tugas yang macet akan dikembalikan ke antrean
}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
