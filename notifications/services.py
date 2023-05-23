import logging
import sys
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Q

from .models import Client #, Task
from .tasks import send_message_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# Функция для запуска рассылки
def run_mailing(mailing):
    logger.info("[mailing_id=%s] Running mailing.", mailing.mailing_id)

    # Фильтруем клиентов по значениям фильтра
    clients = Client.objects.filter(Q(operator_code=mailing.client_filter_operator_code) &
                                    Q(tag=mailing.client_filter_tag))
    logger.info("[mailing_id=%s] Filtered clients: %s.", mailing.mailing_id, clients)

    # Проверяем, если есть клиенты для рассылки
    if not clients:
        logger.info("[mailing_id=%s] No clients found for mailing.", mailing.mailing_id)
        return

    current_time = make_aware(datetime.now())

    # Проверяем, если текущее время больше времени начала и меньше времени окончания рассылки
    if mailing.start_datetime <= current_time <= mailing.end_datetime:
        logger.info("[mailing_id=%s] Mailing is within the specified timeframe: start_datetime=%s, end_datetime=%s.", mailing.mailing_id, mailing.start_datetime, mailing.end_datetime)

        # Запускаем отправку сообщений для каждого клиента
        for client in clients:
            send_message(mailing, client)

    elif mailing.start_datetime > current_time:
        logger.info("[mailing_id=%s] Mailing start time is in the future: start_datetime=%s, end_datetime=%s.", mailing.mailing_id, mailing.start_datetime, mailing.end_datetime)

        # Запускаем отправку сообщений для каждого клиента
        for client in clients:
            # Если время старта в будущем, запланируем автоматический запуск рассылки
            schedule_mailing(mailing, client)


# Функция для отправки сообщения
def send_message(mailing, client):
    logger.info("[message_id=?, client_id=%s, mailing_id=%s] Sending message...", client.client_id, mailing.mailing_id)

    # Вызываем задачу отправки сообщения
    if 'test' in sys.argv:
        send_message_task.delay(mailing.mailing_id, client.client_id, mailing.message_text, client.phone_number, 1, mailing.end_datetime, True)
    else:
        send_message_task.delay(mailing.mailing_id, client.client_id, mailing.message_text, client.phone_number, 1, mailing.end_datetime)


# Функция для запланированного запуска рассылки
def schedule_mailing(mailing, client):
    logger.info("[message_id=?, client_id=%s, mailing_id=%s] Scheduling mailing.", client.client_id, mailing.mailing_id)

    # Вычисляем время до начала рассылки
    delay = mailing.start_datetime - make_aware(datetime.now())

    # Запланировать задачу отправки рассылки с указанным временем задержки
    if 'test' in sys.argv:
        result = send_message_task.apply_async(args=(mailing.mailing_id, client.client_id, mailing.message_text, client.phone_number, 1, mailing.end_datetime, True), countdown=delay.total_seconds())
    else:
        result = send_message_task.apply_async(args=(mailing.mailing_id, client.client_id, mailing.message_text, client.phone_number, 1, mailing.end_datetime), countdown=delay.total_seconds())

    # # Сохраняем идентификатор задачи в модели Task
    # Task.objects.create(
    #     task_id=result.id,
    #     mailing=mailing,
    #     client=client
    # )


