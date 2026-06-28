import json
import datetime
from getpass import getpass
import garminconnect

TOKENSTORE = "~/.garminconnect"

# Try cached tokens; fall back to a full login (handles MFA) if none exist
try:
    garmin = garminconnect.Garmin()
    garmin.login(TOKENSTORE)
    print("Logged in from cached tokens.")
except Exception:
    email = input("Garmin email: ")
    password = getpass("Garmin password: ")
    garmin = garminconnect.Garmin(
        email=email,
        password=password,
        prompt_mfa=lambda: input("MFA code (if prompted): "),
    )
    garmin.login()
    print("Logged in.")

start = datetime.date(2023, 12, 1)
end = datetime.date.today()

print(f"Fetching activities {start} -> {end} ...")
acts = garmin.get_activities_by_date(start.isoformat(), end.isoformat())
print(f"Got {len(acts)} total activities.")

RUN_TYPES = {"running", "track_running", "treadmill_running",
             "trail_running", "virtual_run"}

runs = []
for a in acts:
    if a.get("activityType", {}).get("typeKey") not in RUN_TYPES:
        continue
    dist_m = a.get("distance") or 0
    dur_s = a.get("duration") or 0
    runs.append({
        "id": a.get("activityId"),
        "name": a.get("activityName"),
        "type": a["activityType"]["typeKey"],
        "date": a.get("startTimeLocal"),
        "distance_km": round(dist_m / 1000, 3),
        "duration_s": round(dur_s, 1),
        "avg_pace_s_per_km": round(dur_s / (dist_m / 1000), 1) if dist_m else None,
        "avg_hr": a.get("averageHR"),
        "max_hr": a.get("maxHR"),
        "avg_cadence": a.get("averageRunningCadenceInStepsPerMinute"),
        "elev_gain_m": a.get("elevationGain"),
        "vo2max": a.get("vO2MaxValue"),
    })

runs.sort(key=lambda r: r["date"])
with open("runs.json", "w") as f:
    json.dump(runs, f, indent=2)

print(f"Saved {len(runs)} runs to runs.json")
if runs:
    print("Range:", runs[0]["date"], "->", runs[-1]["date"])