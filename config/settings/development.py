from .base import *  # noqa

DEBUG = True

# Mailer console : affiche les emails dans le terminal au lieu de les envoyer
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

CELERY_TASK_ALWAYS_EAGER = True
