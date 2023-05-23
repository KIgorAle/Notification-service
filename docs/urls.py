from django.urls import path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework import renderers

urlpatterns = [
    path('docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url':'openapi-schema-yaml'}
    ), name='swagger-ui'),
    path('openapi.yaml', get_schema_view(
            title="Notification Service - OpenAPI 3.0",
            renderer_classes=[renderers.OpenAPIRenderer]
        ), name='openapi-schema-yaml'),
    path('openapi.json', get_schema_view(
            title="Notification Service - OpenAPI 3.0",
            renderer_classes = [renderers.JSONOpenAPIRenderer],
        ), name='openapi-schema-json'),
]