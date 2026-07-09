def log_incident(incident):
    print(f"Logging incident: {incident}")
    return {"incident_id": "inc_123", "status": "logged"}

def escalate_incident(incident_id):
    print(f"Escalating incident {incident_id}")
    return {"status": "escalated"}

def resolve_incident(incident_id, resolution):
    print(f"Resolving incident {incident_id} with {resolution}")
    return {"status": "resolved"}

def get_support_status():
    return {"status": "active", "on_call": "team"}