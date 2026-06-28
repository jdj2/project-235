import json, datetime
from getpass import getpass
import garminconnect

g = garminconnect.Garmin(
    input("Garmin email: "),
    getpass("Garmin password: "),
    prompt_mfa=lambda: input("MFA code (if prompted): "),
)
g.login()
print("Logged in.")

# resolve the bits get_rhr_day uses internally, so we can query a full range
try:
    display = g._require_display_name()
except Exception:
    display = getattr(g, "display_name", None)
rhr_base = getattr(g, "garmin_connect_rhr_url", "/userstats-service/wellness/daily")

def windows(s, e, days=330):
    cur = s
    while cur < e:
        nxt = min(cur + datetime.timedelta(days=days), e)
        yield cur, nxt
        cur = nxt + datetime.timedelta(days=1)

start, end = datetime.date(2023, 12, 1), datetime.date.today()
series, raw_sample = {}, None

for ws, we in windows(start, end):
    params = {"fromDate": ws.isoformat(), "untilDate": we.isoformat(), "metricId": 60}
    try:
        data = g.connectapi(f"{rhr_base}/{display}", params=params)
    except Exception as ex:
        print(f"{ws}->{we} failed: {ex}"); continue
    if raw_sample is None: raw_sample = data
    rows = (((data or {}).get("allMetrics") or {}).get("metricsMap") or {}) \
           .get("WELLNESS_RESTING_HEART_RATE") or []
    for row in rows:
        d, v = row.get("calendarDate"), row.get("value")
        if d and v: series[d] = v
    print(f"{ws}->{we}: +{len(rows)} days")

out = [{"date": d, "rhr": series[d]} for d in sorted(series)]
with open("resting_hr.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"Saved {len(out)} resting-HR days to resting_hr.json")
if not out and raw_sample is not None:
    print("NO RHR EXTRACTED — top-level keys:", list(raw_sample.keys()))
    print(json.dumps(raw_sample, indent=2)[:600])
elif out:
    print("SAMPLE:", out[:2])