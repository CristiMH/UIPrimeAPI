from django.contrib import admin
from django.urls import path
from api.views import health_check, send_message, ChatAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/send-message/', send_message, name='send_message'),
    path('api/v1/chat/', ChatAPIView.as_view(), name='chat-api'),
    path("health/", health_check),
]
