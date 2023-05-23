"""
URL configuration for notification_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    # Клиенты
    path('api/clients/', views.ClientListView.as_view(), name='client-list'),
    path('api/clients/create/', views.ClientCreateView.as_view(), name='client-create'),
    path('api/clients/<int:pk>/', views.ClientDetailView.as_view(), name='client-detail'),
    path('api/clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client-update'),
    path('api/clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client-delete'),

    # Рассылки
    path('api/mailings/', views.MailingListView.as_view(), name='mailing-list'),
    path('api/mailings/create/', views.MailingCreateView.as_view(), name='mailing-create'),
    path('api/mailings/<int:pk>/', views.MailingDetailView.as_view(), name='mailing-detail'),
    path('api/mailings/<int:pk>/update/', views.MailingUpdateView.as_view(), name='mailing-update'),
    path('api/mailings/<int:pk>/delete/', views.MailingDeleteView.as_view(), name='mailing-delete'),
    path('api/mailings/stats/', views.mailing_stats, name='mailing-stats'),

    # Сообщения
    path('api/mailings/<int:mailing_id>/messages/', views.MessageListView.as_view(), name='message-list'),
    path('api/messages/', views.MessageListViewFull.as_view(), name='message-list-full'),
]




