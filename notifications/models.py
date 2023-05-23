import pytz
from django.db import models


class Mailing(models.Model):
    mailing_id = models.AutoField(primary_key=True)
    start_datetime = models.DateTimeField()
    message_text = models.TextField()
    client_filter_operator_code = models.CharField(max_length=3)
    client_filter_tag = models.CharField(max_length=255)
    end_datetime = models.DateTimeField()

    def __str__(self):
        return str(self.mailing_id)


class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    phone_number = models.CharField(max_length=11)
    operator_code = models.CharField(max_length=3)
    tag = models.CharField(max_length=255)
    timezone_choices = [(tz, tz) for tz in pytz.all_timezones]
    timezone = models.CharField(max_length=255, choices=timezone_choices)

    def __str__(self):
        return str(self.client_id)


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    created_datetime = models.DateTimeField()
    # created_datetime = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=255)
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.message_id)


# class Task(models.Model):
#     task_id = models.CharField(max_length=255)
#     mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
#     client = models.ForeignKey(Client, on_delete=models.CASCADE)
#
#     def __str__(self):
#         return str(self.task_id)

