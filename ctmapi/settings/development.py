from .base import *
from dotenv import load_dotenv
load_dotenv()
DEBUG = os.getenv('DEBUG')

ALLOWED_HOSTS = ['*']

SECRET_KEY = os.getenv('SECRET_KEY')

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME'),
    'USER': os.getenv('DB_USER'),
    'PASSWORD': os.getenv('DB_PASSWORD'),
    'HOST': os.getenv('DB_HOST'),
    'PORT': '',
  }
}


# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#         # 'rest_framework.authentication.SessionAuthentication',
#         # 'rest_framework.authentication.BasicAuthentication',
#         # 'rest_framework.authentication.TokenAuthentication',
#     ),
# }

MEDIA_ROOT = "C://pycharm/django_project/storage/ctm/media"