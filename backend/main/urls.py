from django.urls import path

from .views import DisplayLogView

app_name = 'main'

urlpatterns = [
    path('api/displaylog/', DisplayLogView.as_view(), name='display_log_view'),
]
