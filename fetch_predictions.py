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

start = datetime.date(2023, 12, 1)
end   = datetime.date.today()

def windows(s, e, days=330):          # stay safely under Garmin's 1-year cap
    cur = s
    while cur < e:
        nxt = min(cur + datetime.timedelta(days=days), e)
        yield cur, nxt
        cur = nxt + datetime.timedelta(days=1)

all_preds = []
for ws, we in windows(start, end):
    for kind in ("monthly", "daily"):
        try:
            out = g.get_race_predictions(ws.isoformat(), we.isoformat(), _type=kind)
            if out:
                all_preds.extend(out)
                print(f"{ws} -> {we}: +{len(out)} ({kind})")
                break
        except Exception as ex:
            print(f"{ws}->{we} {kind} failed: {ex}")

# de-dup by whatever date field each record carries
seen = {}
for p in all_preds:
    key = p.get("calendarDate") or p.get("toCalendarDate") or p.get("fromCalendarDate")
    if key:
        seen[key] = p
preds = list(seen.values())

with open("predictions.json", "w") as f:
    json.dump(preds, f, indent=2)
print(f"Saved {len(preds)} predictions to predictions.json")
if preds:
    print("SAMPLE:", json.dumps(preds[0], indent=2)[:800])