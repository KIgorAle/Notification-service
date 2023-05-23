# from celery.worker.control import revoke
from rest_framework.response import Response
from rest_framework import generics
from django.db.models import Count
from rest_framework.decorators import api_view
import logging

from .models import Client, Mailing, Message #, Task
from .serializers import ClientSerializer, MailingSerializer, MessageSerializer
from .services import run_mailing

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logfile.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class ClientListView(generics.ListAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ClientDetailView(generics.RetrieveAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_create(self, serializer):
        client = serializer.save()
        logger.info("Created client: client_id=%s.", client.client_id)


class ClientUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_update(self, serializer):
        client = serializer.save()
        logger.info("Updated client: client_id=%s.", client.client_id)


class ClientDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_destroy(self, instance):
        client_id = instance.client_id
        instance.delete()
        logger.info("Deleted client: client_id=%s.", client_id)


class MailingListView(generics.ListAPIView):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer


class MailingDetailView(generics.RetrieveAPIView):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer


class MailingCreateView(generics.CreateAPIView):
    serializer_class = MailingSerializer

    def perform_create(self, serializer):
        # Сохраняем рассылку
        mailing = serializer.save()
        logger.info("Created mailing: mailing_id=%s.", mailing.mailing_id)

        # Запускаем рассылку
        run_mailing(mailing)


class MailingUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    def perform_update(self, serializer):
        mailing = serializer.save()
        logger.info("Updated mailing: mailing_id=%s.", mailing.mailing_id)

        # # Отменяем все запланированные задачи для этой рассылки
        # tasks = Task.objects.filter(mailing=mailing).all()
        # for task in tasks:
        #     revoke(state=None, task_id=task.task_id, terminate=True)
        #     logger.info("Revoke mailing: mailing_id=%s, task_id=%s.", mailing.mailing_id, task.task_id)


class MailingDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    def perform_destroy(self, instance):
        mailing_id = instance.mailing_id

        # # Отменяем все запланированные задачи для этой рассылки
        # tasks = Task.objects.filter(mailing=instance)
        # for task in tasks:
        #     revoke(state=None, task_id=task.task_id, terminate=True)
        #     logger.info("Revoke mailing: mailing_id=%s, task_id=%s.", mailing_id, task)

        instance.delete()
        logger.info("Deleted mailing: mailing_id=%s.", mailing_id)


@api_view(['GET'])
def mailing_stats(request):
    mailings = Mailing.objects.prefetch_related('message_set')
    statistics = []

    # Получение всех возможных значений delivery_status
    delivery_statuses = Message.objects.values('delivery_status').distinct()
    status_choices = [status['delivery_status'] for status in delivery_statuses]

    for mailing in mailings:
        message_counts = mailing.message_set.values('delivery_status').annotate(count=Count('delivery_status'))

        mailing_data = {
            "mailing_id": mailing.mailing_id,
            "start_datetime": mailing.start_datetime.isoformat(),
            "message_text": mailing.message_text,
            "client_filter_operator_code": mailing.client_filter_operator_code,
            "client_filter_tag": mailing.client_filter_tag,
            "end_datetime": mailing.end_datetime.isoformat(),
            "messages": {}
        }

        for status_choice in status_choices:
            mailing_data["messages"][status_choice] = {
                "count": 0,
                "data": []
            }

        for message_count in message_counts:
            status = message_count['delivery_status']
            count = message_count['count']
            mailing_data["messages"][status]["count"] = count

        messages = mailing.message_set.all()
        for message in messages:
            message_data = {
                "message_id": message.message_id,
                "created_datetime": message.created_datetime.isoformat(),
                "delivery_status": message.delivery_status,
                "mailing": message.mailing_id,
                "client": message.client_id
            }
            mailing_data["messages"][message.delivery_status]["data"].append(message_data)

        statistics.append(mailing_data)

    return Response(statistics)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        mailing_id = self.kwargs['mailing_id']
        return Message.objects.filter(mailing_id=mailing_id)


class MessageListViewFull(generics.ListAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

