from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-lu6wftg4t2xy_)5y_ex26s1l9_api4(4g3n8)867*houi%nq49'

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
    'app',
    'phonenumber_field',
    'widget_tweaks',
    'django_q',
]

Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 8,
    'timeout': 9999999,
    'retry': 99999999,
    'ack_failures': True,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

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
                'app.context_processors.site_settings',  # Add our custom context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'

# Messages framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
   
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ENA_USERNAME = os.environ.get('ENA_USERNAME')
ENA_USER = os.environ.get('ENA_USER')
ENA_PASSWORD = os.environ.get('ENA_PASSWORD')

# Field encryption key for sensitive data
# In production, generate a key using: from cryptography.fernet import Fernet; print(Fernet.generate_key())
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY', 'zRqxJRkMDpqV9Y5kFdRZvgQNESvHUoQMpGWJqmiDDtY=')

LOCAL_DIR = f"{BASE_DIR}/media/test"
TEMPLATE_DIR = f"{BASE_DIR}/media/test"

JAR_LOCATION = f"{BASE_DIR}/webin-cli-8.1.0.jar"

MAG_NEXTFLOW_COMMAND_STEM = '/net/broker/test/miniconda3/envs/broker/bin/nextflow run hzi-bifo/mag'
MAG_PROFILE = 'singularity'
MAG_ADDITIONAL_OPTIONS = '--skip_prokka --skip_concoct --skip_mhm2 --binqc_tool checkm --skip_spades --skip_spadeshybrid --skip_quast --skip_prodigal --skip_metabat2 --skip_concoct ' # --skip_binqc
MAG_NEXTFLOW_EXECUTOR = 'slurm'
MAG_NEXTFLOW_CLUSTER_OPTIONS = '--qos=broker'
MAG_NEXTFLOW_CLUSTER_CORES = 4
MAG_NEXTFLOW_CLUSTER_MEMORY = '64000'
MAG_NEXTFLOW_CLUSTER_QUEUE = 'cpu'
MAG_NEXTFLOW_CLUSTER_TIME_LIMIT = '1'

PIXELS_PER_CHAR = 8

BIN_CHECKLIST = "ENA_binned_metagenome"
MAG_CHECKLIST = "GSC_MIMAGS"

USE_SLURM_FOR_SUBMG = os.environ.get('USE_SLURM_FOR_SUBMG')

CONDA_PATH = os.environ.get('CONDA_PATH')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}