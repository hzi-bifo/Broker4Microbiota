##################################################
# Docker usage: No edits to this file required, rather, copy TEMPLATE.env to root of Git repo and edit as required; After edits to this file copy settings_DOCKER.py to settings.py
# Local usage:  Make changes to settings_LOCAL.py as required, copy to settings.py
##################################################


from pathlib import Path
import environ
import os

env = environ.Env()
environ.Env.read_env()  # Must be called before os.environ.get()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# https://djecrety.ir/
# SECRET_KEY = '<%= @broker_django_secret_key %>'
# SECRET_KEY = os.environ.get('SECRET_KEY')
SECRET_KEY = ')2^y*ng#pqoj5cor8kmk-_*_l#wmx!_&)qp%as2=)emm#b@3+1'

# ALLOWED_HOSTS = ['<%= @broker_frontend_domain_name %>', '<%= @broker_machine_name %>', '<%= @broker_machine_ip %>']
# ALLOWED_HOSTS = [os.environ.get('DOMAIN_NAME'), os.environ.get('MACHINE_NAME'), os.environ.get('MACHINE_IP')]
ALLOWED_HOSTS = ['broker-demo.bifo.helmholtz-hzi.de', 'dzif-student-0201', '192.168.8.6']

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

TIME_ZONE = 'Europe/Berlin'

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

# SECURITY WARNING: don't run with debug turned on in product
# DEBUG = <%= @broker_django_debug %>
# DEBUG = os.environ.get('DEBUG', "False").lower() in ("true", "1", "yes")
DEBUG = False

# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# FIELD_ENCRYPTION_KEY = '<%= @broker_field_key %>'
# FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY')
FIELD_ENCRYPTION_KEY = 'n686Wou6GKX4H75n4wUtnnoiHFtwSNi65FuGOGi_Ids='

# ENA_USERNAME = '<%= @broker_ena_username %>'
# ENA_USERNAME = os.environ.get('ENA_USERNAME')
ENA_USERNAME = ''

# ENA_USER = '<%= @broker_ena_username %>'
# ENA_USER = os.environ.get('ENA_USER')
ENA_USER = ''

# ENA_PASSWORD = '<%= @broker_ena_password %>'
# ENA_PASSWORD = os.environ.get('ENA_PASSWORD')
ENA_PASSWORD = ''

LOCAL_DIR = f"{BASE_DIR}/media/broker"
TEMPLATE_DIR = f"{LOCAL_DIR}"
JAR_LOCATION = f"{BASE_DIR}/webin-cli-8.1.0.jar"

# CHECKM_REFDATA_DIR = '<%= @broker_checkm_refdata_dir %>'
# CHECKM_REFDATA_DIR = os.environ.get('CHECKM_REFDATA_DIR')
CHECKM_REFDATA_DIR = '/net/broker/checkm_refdata'

# MAG_VERSION  = '<%= @broker_mag_version %>'
# MAG_VERSION = os.environ.get('MAG_VERSION')
MAG_VERSION  = '3.4.0'

# MAG_NEXTFLOW_CLUSTER_OPTIONS  = '<%= @broker_mag_nextflow_cluter_options %>'
# MAG_NEXTFLOW_CLUSTER_OPTIONS = os.environ.get('MAG_NEXTFLOW_CLUSTER_OPTIONS')
MAG_NEXTFLOW_CLUSTER_OPTIONS  = '--qos=broker'

# MAG_NEXTFLOW_CLUSTER_CORES  = '<%= @broker_mag_nextflow_cluter_cores %>'
# MAG_NEXTFLOW_CLUSTER_CORES = os.environ.get('MAG_NEXTFLOW_CLUSTER_CORES')
MAG_NEXTFLOW_CLUSTER_CORES  = '4'

# MAG_NEXTFLOW_CLUSTER_MEMORY  = '<%= @broker_mag_nextflow_cluter_memory %>'
# MAG_NEXTFLOW_CLUSTER_MEMORY = os.environ.get('MAG_NEXTFLOW_CLUSTER_MEMORY')
MAG_NEXTFLOW_CLUSTER_MEMORY  = '64GB'

# MAG_NEXTFLOW_CLUSTER_QUEUE  = '<%= @broker_mag_nextflow_cluter_queue %>'
# MAG_NEXTFLOW_CLUSTER_QUEUE = os.environ.get('MAG_NEXTFLOW_CLUSTER_QUEUE')
MAG_NEXTFLOW_CLUSTER_QUEUE  = 'cpu'

# MAG_NEXTFLOW_CLUSTER_TIME_LIMIT  = '<%= @broker_mag_nextflow_cluter_time_limit %>'
# MAG_NEXTFLOW_CLUSTER_TIME_LIMIT = os.environ.get('MAG_NEXTFLOW_CLUSTER_TIME_LIMIT')
MAG_CLUSTER_TIME_LIMIT  = '12'

MAG_NEXTFLOW_COMMAND_STEM = '{BASE_DIR}/../../miniconda3/envs/broker/bin/nextflow run hzi-bifo/mag - r {MAG_VERSION}'
MAG_PROFILE = 'singularity'
MAG_ADDITIONAL_OPTIONS = '-c {BASE_DIR}/../checkm_mem_increase.nf --skip_prokka --skip_concoct --skip_mhm2 --checkm_db {CHECKM_REFDATA_DIR} --binqc_tool checkm --skip_spades --skip_spadeshybrid --skip_quast --skip_prodigal --skip_metabat2 --skip_gtdbtk'
MAG_NEXTFLOW_EXECUTOR = 'slurm'

# CSRF_TRUSTED_ORIGINS = ["https://<%= @broker_frontend_domain_name %>"]
# CSRF_TRUSTED_ORIGINS = [os.environ.get('CSRF_TRUSTED_ORIGINS')]
CSRF_TRUSTED_ORIGINS = ["https://broker-demo.bifo.helmholtz-hzi.de"]

PIXELS_PER_CHAR = 8

BIN_CHECKLIST = "ENA_binned_metagenome"
MAG_CHECKLIST = "GSC_MIMAGS"

# USE_SLURM_FOR_SUBMG = <%= @use_slurm_for_submg %>
# USE_SLURM_FOR_SUBMG = os.environ.get('USE_SLURM_FOR_SUBMG', "False").lower() in ("true", "1", "yes")
USE_SLURM_FOR_SUBMG = True

# CONDA_PATH = '<%= @conda_path %>'
# CONDA_PATH = os.environ.get('CONDA_PATH')
CONDA_PATH = '{BASE_DIR}/../../miniconda3'

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

# MAG_NEXTFLOW_STUB_MODE = <%= @mag_nextflow_stub_mode %>
# MAG_NEXTFLOW_STUB_MODE = os.environ.get('MAG_NEXTFLOW_STUB_MODE', "False").lower() in ("true", "1", "yes")
MAG_NEXTFLOW_STUB_MODE = True

# AUTO_CREATE_USERS_AS_ADMIN = <%= @auto_create_users_as_admin %>
# AUTO_CREATE_USERS_AS_ADMIN = os.environ.get('AUTO_CREATE_USERS_AS_ADMIN', "False").lower() in ("true", "1", "yes")
AUTO_CREATE_USERS_AS_ADMIN = True

