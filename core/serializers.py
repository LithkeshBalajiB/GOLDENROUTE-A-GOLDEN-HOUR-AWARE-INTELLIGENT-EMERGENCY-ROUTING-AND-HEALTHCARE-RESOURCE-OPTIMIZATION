from rest_framework import serializers
from .models import Hospital, EmergencyCase

class HospitalSerializer(serializers.ModelSerializer):
    available_er_rooms = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = '__all__'

    def get_available_er_rooms(self, obj):
        return obj.available_er_rooms()


class EmergencyCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyCase
        fields = '__all__'
