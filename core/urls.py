from django.urls import path
from . import views

urlpatterns = [

    path("login/", views.login_view, name="login"),
    path("ambulance/", views.ambulance_dashboard, name="ambulance_dashboard"),
    path("hospital/", views.hospital_dashboard, name="hospital_dashboard"),

    path("citizen/", views.citizen_dashboard, name="citizen_dashboard"),

    # Citizen signup
    path("citizen-signup/", views.citizen_signup, name="citizen_signup"),

    path("edit-profile/", views.edit_health_profile, name="edit_health_profile"),
    path("distress/", views.distress_signal, name="distress_signal"),
]