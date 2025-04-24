from django.apps import AppConfig
from corsheaders.signals import check_request_enabled
from django.dispatch import receiver


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        @receiver(check_request_enabled)
        def cors_allow_health_check(sender, request, **kwargs):
            return request.path == "/health/"