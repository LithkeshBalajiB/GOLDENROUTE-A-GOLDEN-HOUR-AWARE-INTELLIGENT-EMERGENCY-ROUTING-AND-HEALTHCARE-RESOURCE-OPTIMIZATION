from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import PatientTransfer, HealthProfile
from .models import (
    Hospital,
    EmergencyCase,
    TrafficInput,
    HealthProfile,
    PatientTransfer,
    UserProfile
)
from django.utils import timezone
from .utils import calculate_hospital_score, get_travel_time
from math import sqrt
from .models import DistressSignal


@login_required
def distress_signal(request):

    if request.method == "POST":

        lat = float(request.POST.get("lat"))
        lng = float(request.POST.get("lng"))

        citizen = HealthProfile.objects.get(user=request.user)

        # find nearest ambulance
        ambulances = UserProfile.objects.filter(role="ambulance")

        nearest = None
        min_distance = 999999

        for amb in ambulances:

            if amb.latitude and amb.longitude:

                dist = sqrt(
                    (lat - amb.latitude) ** 2 +
                    (lng - amb.longitude) ** 2
                )

                if dist < min_distance:
                    min_distance = dist
                    nearest = amb

        signal = DistressSignal.objects.create(
            citizen=citizen,
            latitude=lat,
            longitude=lng,
            assigned_ambulance=nearest.user if nearest else None,
            emergency_phone=citizen.emergency_contact
        )

        return redirect("citizen_dashboard")

# =========================
# LOGIN
# =========================
def login_view(request):

    last_citizen = request.session.get("last_citizen")

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            role = user.userprofile.role

            if role == "ambulance":
                return redirect("ambulance_dashboard")

            elif role == "hospital":
                return redirect("hospital_dashboard")

            elif role == "citizen":
                return redirect("citizen_dashboard")

    return render(request, "core/login.html", {
        "last_citizen": last_citizen
    })


# =========================
# CITIZEN SIGNUP
# =========================
def citizen_signup(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        UserProfile.objects.create(
            user=user,
            role="citizen"
        )

        return redirect("login")

    return render(request, "core/citizen_signup.html")


# =========================
# CITIZEN DASHBOARD
# =========================
@login_required
def citizen_dashboard(request):

    profile = HealthProfile.objects.filter(user=request.user).first()

    return render(request, "core/citizen_dashboard.html", {
        "profile": profile
    })


# =========================
# EDIT HEALTH PROFILE
# =========================
@login_required
def edit_health_profile(request):

    profile = HealthProfile.objects.filter(user=request.user).first()

    if request.method == "POST":

        name = request.POST.get("name")
        aadhar = request.POST.get("aadhar_number")
        comments = request.POST.get("comments")

        age = request.POST.get("age")
        blood_group = request.POST.get("blood_group")

        diabetes = "diabetes" in request.POST
        heart_disease = "heart_disease" in request.POST

        emergency_contact = request.POST.get("emergency_contact")

        if profile:

            profile.name = name
            profile.aadhar_number = aadhar
            profile.comments = comments
            profile.age = age
            profile.blood_group = blood_group
            profile.diabetes = diabetes
            profile.heart_disease = heart_disease
            profile.emergency_contact = emergency_contact
            profile.save()

        else:

            profile = HealthProfile.objects.create(
                user=request.user,
                name=name,
                aadhar_number=aadhar,
                comments=comments,
                age=age,
                blood_group=blood_group,
                diabetes=diabetes,
                heart_disease=heart_disease,
                emergency_contact=emergency_contact
            )

        request.session["last_citizen"] = {
            "name": name,
            "aadhar": aadhar
        }

        return redirect("citizen_dashboard")

    return render(request, "core/edit_health_profile.html", {
        "profile": profile
    })


# =========================
# AMBULANCE DASHBOARD
# =========================
@login_required
def ambulance_dashboard(request):

    # Ensure only ambulance users access
    if request.user.userprofile.role != "ambulance":
        return redirect("login")

    profile = request.user.userprofile

    hospitals = Hospital.objects.all()

    best_hospital = None
    ambulance_lat = profile.latitude
    ambulance_lng = profile.longitude
    patient_type = None

    # =========================
    # UPDATE AMBULANCE LOCATION
    # =========================
    if request.method == "POST" and "update_location" in request.POST:

        lat = request.POST.get("current_lat")
        lng = request.POST.get("current_lng")

        if lat and lng:
            profile.latitude = float(lat)
            profile.longitude = float(lng)
            profile.location_updated_at = timezone.now()
            profile.save()

        return redirect("ambulance_dashboard")

    # =========================
    # FIND HOSPITALS
    # =========================
    if request.method == "POST" and "find_hospitals" in request.POST:

        patient_type = request.POST.get("patient_type")

        ambulance_lat = float(request.POST.get("ambulance_lat"))
        ambulance_lng = float(request.POST.get("ambulance_lng"))

        best_score = -999

        for hospital in hospitals:

            if hospital.er_rooms_available <= 0:
                hospital.eta = None
                continue

            if hospital.icu_beds_available <= 0:
                hospital.eta = None
                continue

            if not hospital.has_specialist(patient_type):
                hospital.eta = None
                continue

            result = get_travel_time(
                ambulance_lat,
                ambulance_lng,
                hospital.latitude,
                hospital.longitude
            )

            if result is None:
                hospital.eta = None
                continue

            eta = result["duration_minutes"]
            hospital.eta = round(eta, 1)

            score = calculate_hospital_score(hospital, patient_type, eta)

            if score > best_score:
                best_score = score
                best_hospital = hospital

    # =========================
    # CONFIRM HOSPITAL
    # =========================
    if request.method == "POST" and "confirm_hospital" in request.POST:

        hospital_id = request.POST.get("hospital_id")
        aadhar = request.POST.get("aadhar_number")
        patient_type = request.POST.get("patient_type")

        ambulance_lat = float(request.POST.get("ambulance_lat"))
        ambulance_lng = float(request.POST.get("ambulance_lng"))

        hospital = Hospital.objects.get(id=hospital_id)

        citizen = HealthProfile.objects.filter(
            aadhar_number=aadhar
        ).first()

        if citizen:

            result = get_travel_time(
                ambulance_lat,
                ambulance_lng,
                hospital.latitude,
                hospital.longitude
            )

            eta = None

            if result:
                eta = result["duration_minutes"]

            PatientTransfer.objects.create(
                hospital=hospital,
                citizen=citizen,
                ambulance_user=request.user,
                patient_type=patient_type,
                eta_minutes=eta
            )

        EmergencyCase.objects.create(
            patient_type=patient_type,
            ambulance_user=request.user,
            selected_hospital=hospital
        )

        best_hospital = hospital

    # =========================
    # DISTRESS SIGNALS
    # =========================
    signals = DistressSignal.objects.filter(
        assigned_ambulance=request.user
    ).order_by("-created_at")

    return render(request, "core/ambulance_dashboard.html", {
        "hospitals": hospitals,
        "best_hospital": best_hospital,
        "ambulance_lat": ambulance_lat,
        "ambulance_lng": ambulance_lng,
        "patient_type": patient_type,
        "signals": signals
    })
# =========================
# HOSPITAL DASHBOARD
# =========================
@login_required
def hospital_dashboard(request):

    # Only hospital users allowed
    if request.user.userprofile.role != "hospital":
        return redirect("login")

    # Find hospital connected to logged-in user
    hospital = Hospital.objects.filter(user=request.user).first()

    if not hospital:
        return render(request, "core/hospital_dashboard.html", {
            "error": "No hospital linked to this account."
        })

    # Get incoming patients
    transfers = PatientTransfer.objects.filter(
        hospital=hospital
    ).order_by("-sent_time")

    # Update hospital resources
    if request.method == "POST":

        hospital.er_rooms_available = int(
            request.POST.get("er_rooms_available", 0)
        )

        hospital.icu_beds_available = int(
            request.POST.get("icu_beds_available", 0)
        )

        hospital.cardiologist_available = "cardio" in request.POST
        hospital.neurosurgeon_available = "neuro" in request.POST
        hospital.trauma_team_available = "trauma" in request.POST

        hospital.save()

    return render(request, "core/hospital_dashboard.html", {
        "hospital": hospital,
        "transfers": transfers
    })