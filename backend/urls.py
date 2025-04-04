from django.contrib import admin
from django.urls import path
from api.views import send_message, keep_alive

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/send-message/', send_message, name='send_message'),
    path('api/v1/keep-alive/', keep_alive, name='keep_alive'),
]
