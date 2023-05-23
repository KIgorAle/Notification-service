from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    return Response({
        "Clients": {
            "clients": reverse("client-list", request=request, format=format),
            "client-create": reverse("client-create", request=request, format=format),
            "client-detail": "api/clients/<int:client_id>/",
            "client-update": "api/clients/<int:client_id>/update/",
            "client-delete": "api/clients/<int:client_id>/delete/",

            "Examples": {
                "first client-detail": reverse("client-detail", request=request, format=format, kwargs={'pk': 1}),
                "first client-update": reverse("client-update", request=request, format=format, kwargs={'pk': 1}),
                "first client-delete": reverse("client-delete", request=request, format=format, kwargs={'pk': 1}),
            }
        },
        "Mailings": {
            "mailings": reverse("mailing-list", request=request, format=format),
            "mailing-create": reverse("mailing-create", request=request, format=format),
            "mailing-detail": "api/mailings/<int:mailing_id>/",
            "mailing-update": "api/mailings/<int:mailing_id>/update/",
            "mailing-delete": "api/mailings/<int:mailing_id>/delete/",

            "Examples": {
                "first mailing-detail": reverse("mailing-detail", request=request, format=format, kwargs={'pk': 1}),
                "first mailing-update": reverse("mailing-update", request=request, format=format, kwargs={'pk': 1}),
                "first mailing-delete": reverse("mailing-delete", request=request, format=format, kwargs={'pk': 1}),
            },
            "mailing-stats": reverse("mailing-stats", request=request, format=format),
        },
        "Messages": {
            "messages by mailing_id": "api/mailings/<int:mailing_id>/messages/",
            "Examples": {
                "messages by mailing_id = 1": reverse("message-list", request=request, format=format,  kwargs={'mailing_id': 1}),
            },
            "messages": reverse("message-list-full", request=request, format=format),
        }

    })