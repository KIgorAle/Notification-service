import logging
import pytz
import requests
from celery import shared_task
from datetime import datetime
from .models import Message, Mailing, Client


JWT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTQ4MzU2MzAsImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6Imh0dHBzOi8vdC5tZS9NZXRhSWdvciJ9.ecip6qypuY9X2YW_soqOrNcyVUHcNOlxLBFCHMU7AXA'
API_BASE_URL = 'https://probe.fbrq.cloud/v1/send/'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def get_delay(attempt):
    if attempt == 1:
        return 60  # 1 минута
    elif attempt == 2:
        return 300  # 5 минут
    elif attempt == 3:
        return 1800  # 30 минут
    elif attempt == 4:
        return 3600  # 1 час
    elif attempt == 5:
        return 10800  # 3 часа
    elif attempt == 6:
        return 21600  # 6 часов
    elif attempt == 7:
        return 43200  # 12 часов
    elif attempt == 8:
        return 86400  # 24 часа
    elif attempt == 9:
        return 64800  # 18 часов
    elif attempt == 10:
        return 7200  # 2 часа
    else:
        return 0  # По умолчанию


@shared_task
def send_message_task(mailing_id, client_id, message_text, phone_number, attempt, end_datetime, is_test=False):

    if is_test:
        db = 'test'
    else:
        db = 'default'

    logger.info("[message_id=?, client_id=%s, mailing_id=%s] Sending message task, attempt=%s.", client_id, mailing_id, attempt)

    # Получаем объект Mailing по идентификатору
    mailing = Mailing.objects.using(db).get(mailing_id=mailing_id)

    timezone = pytz.timezone('Europe/Moscow')

    current_time = timezone.localize(datetime.now()).isoformat()

    if end_datetime >= current_time:
        # Получаем объект Client по идентификатору
        client = Client.objects.using(db).get(client_id=client_id)
        # Создаем новую запись в сущности "сообщение" с соответствующими атрибутами
        message = Message.objects.using(db).create(
            created_datetime=datetime.now(),
            delivery_status='pending',
            mailing=mailing,
            client=client
        )

        logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Created message.", message.message_id, client_id, mailing_id)

        # Отправка запроса к внешнему сервису для отправки сообщения
        try:
            # Формируем данные для запроса
            payload = {
                'id': int(message.message_id),
                "phone": int(phone_number),
                "text": str(message_text)
            }

            headers = {
                'Authorization': f'Bearer {JWT_TOKEN}',
                'Content-Type': 'application/json'
            }

            # Отправляем POST-запрос к API внешнего сервиса
            logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Sending request to external service: URL=%s, payload=%s.", message.message_id, client_id, mailing_id, f'{API_BASE_URL}{payload["id"]}', payload)
            response = requests.post(f'{API_BASE_URL}{payload["id"]}', json=payload, headers=headers)

            logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Response status code: %s.", message.message_id, client_id, mailing_id, response.status_code)
            logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Response body: %s.", message.message_id, client_id, mailing_id, response.json())

            if response.status_code == 200:
                # Обновляем статус доставки сообщения в базе данных
                message.delivery_status = 'delivered'
            else:
                message.delivery_status = 'error'

                if attempt <= 10:
                    delay = get_delay(attempt)
                    # Отложенная повторная отправка задачи через delay секунд
                    logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Scheduling retry task: attempt=%s, delay=%s.", message.message_id, client_id, mailing_id, attempt + 1, delay)

                    if is_test:
                        send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1, True], countdown=delay)
                    else:
                        send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1], countdown=delay)

        except requests.exceptions.RequestException as e:
            # Обработка ошибок сети или недоступности внешнего сервиса
            message.delivery_status = 'error'

            logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Error occurred during message delivery: %s.", message.message_id, client_id, mailing_id, str(e))

            if attempt <= 10:
                delay = get_delay(attempt)
                # Отложенная повторная отправка задачи через delay секунд
                logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Scheduling retry task: attempt=%s, delay=%s.", message.message_id, client_id, mailing_id, attempt + 1, delay)

                if is_test:
                    send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1, True], countdown=delay)
                else:
                    send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1], countdown=delay)

        except Exception as e:
            # Обработка других исключений
            message.delivery_status = 'error'

            logger.info("[message_id=%s, client_id=%s, mailing_id=%s] An error occurred: %s.", message.message_id, client_id, mailing_id, str(e))

            if attempt <= 10:
                delay = get_delay(attempt)
                # Отложенная повторная отправка задачи через delay секунд
                logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Scheduling retry task: attempt=%s, delay=%s.", message.message_id, client_id, mailing_id, attempt + 1, delay)

                if is_test:
                    send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1, True], countdown=delay)
                else:
                    send_message_task.apply_async(args=[mailing_id, client_id, message_text, phone_number, attempt + 1], countdown=delay)

        # Сохранение обновленного статуса доставки сообщения
        message.save()
        logger.info("[message_id=%s, client_id=%s, mailing_id=%s] Saved message.", message.message_id, client_id, mailing_id)
    else:
        logger.info("[message_id=None, client_id=%s, mailing_id=%s] Time limit exceeded.", client_id, mailing_id)
