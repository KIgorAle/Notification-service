from datetime import timedelta, datetime

import pytz
from django.test import Client
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from .models import Client as ModelClient, Mailing, Message
import json
import time


class APITestCase(TransactionTestCase):
    def setUp(self):
        ModelClient.objects.all().delete()
        Mailing.objects.all().delete()
        Message.objects.all().delete()

        self.client = Client()

    def test_create_clients(self):
        # Создаем пять клиентов с разными данными
        data = [
            {'phone_number': '79151111111', 'operator_code': '915', 'tag': 'tag1', 'timezone': 'Europe/Moscow'},
            {'phone_number': '79142222222', 'operator_code': '914', 'tag': 'tag2', 'timezone': 'Europe/Berlin'},
            {'phone_number': '79133333333', 'operator_code': '913', 'tag': 'tag3', 'timezone': 'Asia/Tokyo'},
            {'phone_number': '79264444444', 'operator_code': '926', 'tag': 'tag4', 'timezone': 'America/New_York'},
            {'phone_number': '79175555555', 'operator_code': '917', 'tag': 'tag5', 'timezone': 'America/Los_Angeles'},

            {'phone_number': '89175555555', 'operator_code': '917', 'tag': 'tag5', 'timezone': 'America/Los_Angeles'},
            {'phone_number': '79175555555', 'operator_code': '917', 'tag': 'tag5', 'timezone': '12345'},
            {'phone_number': '79175555555', 'operator_code': 'ydj', 'tag': 'tag5', 'timezone': 'America/Los_Angeles'},
            {'phone_number': '7dfd5555555', 'operator_code': 'dfd', 'tag': 'tag5', 'timezone': 'grereregre'},
        ]

        resp_json = []

        for i in range(0, 5):
            response = self.client.post(reverse('client-create'), json.dumps(data[i]), content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            resp_json.append(response.json())
            self.assertDictEqual(data[i], {k: v for k, v in resp_json[i].items() if k != 'client_id'})

        fail_resp_json = [
            {'phone_number': ['Неправильный формат номера телефона']},
            {'timezone': ['Значения 12345 нет среди допустимых вариантов.']},
            {'operator_code': ['Неправильный формат кода оператора']},
            {'phone_number': ['Неправильный формат номера телефона'], 'operator_code': ['Неправильный формат кода оператора'], 'timezone': ['Значения grereregre нет среди допустимых вариантов.']},
        ]

        for i in range(5, 9):
            response = self.client.post(reverse('client-create'), json.dumps(data[i]), content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            resp_json.append(response.json())
            self.assertEqual(resp_json[i], fail_resp_json[i-5])

        # Проверяем, что созданы пять клиентов
        response = self.client.get(reverse('client-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clients = response.json()
        self.assertEqual(len(clients), 5)

        # Редактируем первых двух клиентов
        response = self.client.put(reverse('client-update', kwargs={'pk': resp_json[0]['client_id']}), json.dumps({'phone_number': '79141111111', 'operator_code': '914', 'tag': 'updated_tag', 'timezone': 'Europe/Moscow'}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(reverse('client-update', kwargs={'pk': resp_json[1]['client_id']}), json.dumps({'tag': 'updated_tag'}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Удаляем третьего клиента
        response = self.client.delete(reverse('client-delete', kwargs={'pk': resp_json[2]['client_id']}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что осталось 4 клиента
        response = self.client.get(reverse('client-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clients = response.json()
        self.assertEqual(len(clients), 4)

        # Проверяем, что у двух клиентов одинаковые метки и коды оператора
        response = self.client.get(reverse('client-detail', kwargs={'pk': resp_json[0]['client_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client_1 = response.json()

        response = self.client.get(reverse('client-detail', kwargs={'pk': resp_json[1]['client_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client_2 = response.json()

        self.assertEqual(client_1['tag'], client_2['tag'])
        self.assertEqual(client_1['operator_code'], client_2['operator_code'])

    def test_create_mailings(self):
        data = [
            {'phone_number': '79141111111', 'operator_code': '914', 'tag': 'updated_tag', 'timezone': 'Europe/Moscow'},
            {'phone_number': '79142222222', 'operator_code': '914', 'tag': 'updated_tag', 'timezone': 'Europe/Berlin'},
            {'phone_number': '79264444444', 'operator_code': '926', 'tag': 'tag4', 'timezone': 'America/New_York'},
            {'phone_number': '79175555555', 'operator_code': '917', 'tag': 'tag5', 'timezone': 'America/Los_Angeles'},
        ]

        for item in data:
            response = self.client.post(reverse('client-create'), json.dumps(item), content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Создаем рассылку, которая началась вчера и закончится завтра
        timezone = pytz.timezone('Europe/Moscow')
        resp_json = []

        data = [
            {'start_datetime': timezone.localize(datetime.now() - timedelta(days=1)).isoformat(), 'message_text': 'Test message 1', 'client_filter_operator_code': '914', 'client_filter_tag': 'updated_tag', 'end_datetime': timezone.localize(datetime.now() + timedelta(days=1)).isoformat()},
            {'start_datetime': timezone.localize(datetime.now() + timedelta(minutes=2)).isoformat(), 'message_text': 'Test message 2', 'client_filter_operator_code': '926', 'client_filter_tag': 'tag4', 'end_datetime': timezone.localize(datetime.now() + timedelta(days=1)).isoformat()},
            {'start_datetime': timezone.localize(datetime.now() - timedelta(days=2)).isoformat(), 'message_text': 'Test message 3', 'client_filter_operator_code': '926', 'client_filter_tag': 'tag4', 'end_datetime': timezone.localize(datetime.now() - timedelta(days=1)).isoformat()},
            {'start_datetime': timezone.localize(datetime.now() - timedelta(days=1)).isoformat(), 'message_text': 'Test message 4', 'client_filter_operator_code': '999', 'client_filter_tag': 'tag5', 'end_datetime': timezone.localize(datetime.now() + timedelta(days=1)).isoformat()}

        ]

        response = self.client.post(reverse('mailing-create'), json.dumps(data[0]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resp_json.append(response.json())
        self.assertDictEqual(data[0], {k: v for k, v in resp_json[0].items() if k != 'mailing_id'})

        # Проверяем, что создалась одна рассылка
        response = self.client.get(reverse('mailing-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mailings = response.json()
        self.assertEqual(len(mailings), 1)

        # Создаем вторую рассылку, которая начнется через 2 минуты
        response = self.client.post(reverse('mailing-create'), json.dumps(data[1]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resp_json.append(response.json())
        self.assertDictEqual(data[1], {k: v for k, v in resp_json[1].items() if k != 'mailing_id'})

        # Проверяем, что создалась вторая рассылка
        response = self.client.get(reverse('mailing-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mailings = response.json()
        self.assertEqual(len(mailings), 2)

        # Получаем объекты рассылок
        response = self.client.get(reverse('mailing-detail', kwargs={'pk': resp_json[0]['mailing_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mailing_1 = response.json()

        response = self.client.get(reverse('mailing-detail', kwargs={'pk': resp_json[1]['mailing_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mailing_2 = response.json()

        # Проверяем, что осталось 4 клиента
        response = self.client.get(reverse('client-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clients = response.json()
        self.assertEqual(len(clients), 4)

        # Получаем сообщения по первой рассылке
        time.sleep(10)  # Ждем 10 секунд перед получением сообщений
        response = self.client.get(reverse('message-list', kwargs={'mailing_id': mailing_1['mailing_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 2)

        # Получаем сообщения по второй рассылке
        time.sleep(180)  # Ждем 3 минуты
        response = self.client.get(reverse('message-list', kwargs={'mailing_id': mailing_2['mailing_id']}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 1)

        # Проверяем, что всего создались 3 сообщения
        response = self.client.get(reverse('message-list-full'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 3)

        # Создаем рассылку с датой начала в прошлом
        response = self.client.post(reverse('mailing-create'), json.dumps(data[2]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mailing_id = response.json()['mailing_id']

        # Ждем 10 секунд
        time.sleep(10)

        # Проверяем, что сообщения не были созданы
        response = self.client.get(reverse('message-list', kwargs={'mailing_id': mailing_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 0)

        # Создаем рассылку без соответствующего клиента
        response = self.client.post(reverse('mailing-create'), json.dumps(data[3]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mailing_id = response.json()['mailing_id']

        # Ждем 10 секунд
        time.sleep(10)

        # Проверяем, что сообщения не были созданы
        response = self.client.get(reverse('message-list', kwargs={'mailing_id': mailing_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        messages = response.json()
        self.assertEqual(len(messages), 0)

        # Обновляем рассылку
        data[3]['message_text'] = 'Updated test message'
        response = self.client.patch(reverse('mailing-update', kwargs={'pk': mailing_id}), json.dumps(data[3]), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что рассылка обновилась
        response = self.client.get(reverse('mailing-detail', kwargs={'pk': mailing_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mailing = response.json()
        self.assertEqual(mailing['message_text'], data[3]['message_text'])

        # Удаляем рассылку
        response = self.client.delete(reverse('mailing-delete', kwargs={'pk': mailing_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что рассылка была удалена
        response = self.client.get(reverse('mailing-detail', kwargs={'pk': mailing_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(reverse('mailing-stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

