from django.contrib import admin
from django.urls import path
from api.views import send_message

urlpatterns = [
    path('admin/', admin.site.urls),
    path('send-message/', send_message, name='send_message'),
]
