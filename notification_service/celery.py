from __future__ import absolute_import, unicode_literals
import os

from celery import Celery

# Переменная окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')

# Экземпляр Celery и имя проекта
app = Celery('notification_service')

# Загрузка настроек из переменной окружения DJANGO_SETTINGS_MODULE
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматический поиск и регистрация задач в файле tasks.py
app.autodiscover_tasks(['notifications'])


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
