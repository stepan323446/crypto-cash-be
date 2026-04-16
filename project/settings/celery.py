import os
import sys

from django.conf import settings

TESTING = 'test' in sys.argv
TESTING = TESTING or 'test_coverage' in sys.argv or 'pytest' in sys.modules

CELERY_BROKER_URL = f"amqp://{os.environ['RABBITMQ_USER']}:{os.environ['RABBITMQ_PASSWORD']}@{os.environ['RABBITMQ_HOST']}:{os.environ['RABBITMQ_PORT']}/{os.environ['RABBITMQ_VHOST']}"

CELERY = {
    'broker_url': CELERY_BROKER_URL,
    'task_always_eager': TESTING,
    'result_extended': True,
    'timezone': settings.TIME_ZONE,
    'result_backend': os.getenv("DJANGO_REDIS_LOCATION", "redis://redis:6379") + "/1",
    'task_track_started': True
}