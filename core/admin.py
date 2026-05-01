from django.contrib import admin
from .models import (
    Hospital,
    EmergencyCase,
    TrafficInput,
    HealthProfile,
    PatientTransfer,
    UserProfile
)

admin.site.register(Hospital)
admin.site.register(EmergencyCase)
admin.site.register(TrafficInput)
admin.site.register(HealthProfile)
admin.site.register(PatientTransfer)
admin.site.register(UserProfile)