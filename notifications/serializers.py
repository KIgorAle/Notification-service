from rest_framework import serializers
from .models import Client, Mailing, Message
from rest_framework.exceptions import ValidationError
import re


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

    def validate_phone_number(self, value):
        if not re.match(r'^7\d{10}$', value):
            raise ValidationError("Неправильный формат номера телефона")
        return value

    def validate_operator_code(self, value):
        if not re.match(r'^\d{3}$', value):
            raise ValidationError("Неправильный формат кода оператора")
        return value


class MailingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mailing
        fields = '__all__'

    def validate_client_filter_operator_code(self, value):
        if not re.match(r'^\d{3}$', value):
            raise ValidationError("Неправильный формат кода оператора")
        return value

    def validate(self, attrs):
        if attrs['end_datetime'] <= attrs['start_datetime']:
            raise ValidationError("Значение end_datetime должно быть больше значения start_datetime")
        return attrs


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

