from django.db import models
from django.contrib.auth.models import User


# =========================
# User Profile (Role System)
# =========================
class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('ambulance', 'Ambulance Driver'),
        ('hospital', 'Hospital'),
        ('citizen', 'Common Citizen'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_updated_at = models.DateTimeField(
        null=True,
        blank=True
    )
    def __str__(self):
        return f"{self.user.username} ({self.role})"


# =========================
# Citizen Health Profile
# =========================
class HealthProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Basic identity
    name = models.CharField(max_length=200)

    # Aadhaar must be unique
    aadhar_number = models.CharField(
        max_length=12,
        unique=True
    )

    comments = models.TextField(blank=True)

    # Optional medical data
    age = models.IntegerField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    diabetes = models.BooleanField(default=False)
    heart_disease = models.BooleanField(default=False)

    emergency_contact = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.name


# =========================
# Hospital
# =========================
class Hospital(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)

    er_rooms_available = models.IntegerField(default=0)
    icu_beds_available = models.IntegerField(default=0)

    cardiologist_available = models.BooleanField(default=False)
    neurosurgeon_available = models.BooleanField(default=False)
    trauma_team_available = models.BooleanField(default=False)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    # Check if the hospital has required specialist
    def has_specialist(self, patient_type):

        mapping = {
            "cardiac": self.cardiologist_available,
            "neuro": self.neurosurgeon_available,
            "trauma": self.trauma_team_available,
        }

        return mapping.get(patient_type, True)


# =========================
# Emergency Case
# =========================
class EmergencyCase(models.Model):

    patient_type = models.CharField(max_length=50)

    ambulance_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    selected_hospital = models.ForeignKey(
        Hospital,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Case ({self.patient_type}) by {self.ambulance_user.username}"


# =========================
# Traffic Input
# =========================
class TrafficInput(models.Model):

    case = models.ForeignKey(
        EmergencyCase,
        on_delete=models.CASCADE
    )

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE
    )

    travel_time_minutes = models.FloatField()

    def __str__(self):
        return f"{self.case} -> {self.hospital} ({self.travel_time_minutes} mins)"
    
# =========================
# Patient Transfer
class PatientTransfer(models.Model):

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE
    )

    citizen = models.ForeignKey(
        HealthProfile,
        on_delete=models.CASCADE
    )

    ambulance_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    patient_type = models.CharField(max_length=50)
    eta_minutes = models.FloatField(null=True, blank=True)
    sent_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.citizen.name} → {self.hospital.name}"
    
class DistressSignal(models.Model):

    citizen = models.ForeignKey(
        HealthProfile,
        on_delete=models.CASCADE
    )

    latitude = models.FloatField()
    longitude = models.FloatField()

    assigned_ambulance = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    emergency_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Distress from {self.citizen.name}"