import requests

API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjFjMzA0MzBlNGNiMDQxZGVhNDcwZmIzNDYzNjQwNjhhIiwiaCI6Im11cm11cjY0In0="

def get_travel_time(start_lat, start_lng, end_lat, end_lng):

    url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [start_lng, start_lat],  # Ambulance location
            [end_lng, end_lat]       # Hospital location
        ]
    }

    response = requests.post(url, json=body, headers=headers)

    if response.status_code == 200:
        data = response.json()
        duration_seconds = data['routes'][0]['summary']['duration']
        distance_meters = data['routes'][0]['summary']['distance']

        return {
            "duration_minutes": duration_seconds / 60,
            "distance_km": distance_meters / 1000
        }

    else:
        print("API Error:", response.text)
        return None


def calculate_hospital_score(hospital, patient_type, travel_time):
    score = 0

    # 🚑 ER availability score
    score += hospital.er_rooms_available * 3

    # 🏥 ICU availability score
    score += hospital.icu_beds_available * 2

    # 👨‍⚕️ Specialist bonus
    if hospital.has_specialist(patient_type):
        score += 20
    else:
        score -= 20  # Penalize if specialist missing

    # ⏱ Travel time penalty (less time = better score)
    score -= travel_time * 1.5

    return score