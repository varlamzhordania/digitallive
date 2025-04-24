from rest_framework import serializers

from .models import DisplayLog


class DisplayLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisplayLog
        fields = ['display', 'type', 'message']
