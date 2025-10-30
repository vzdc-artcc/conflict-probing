import time

from config import print_config_vars, REPEAT_TIME
from conflict_probing import get_aircraft_conflict_status

if __name__ == "__main__":
    start = time.time()
    print("-----------------------------------------------")
    print("VATSIM Collision Probing (FAA Only)")
    print("-----------------------------------------------")
    print()
    print("Configuration:")
    print_config_vars()
    print()
    # print()
    while True:
        print("-----------------------------------------------")
        conflicting, non_conflicting, timestamp = get_aircraft_conflict_status()
        if len(conflicting) == 0:
            print("No alerts detected!")
        else:
            for aircraft in conflicting:
                print(f"{aircraft['callsign']} <-> {aircraft['conflicting_callsign']}: {aircraft['conflict_level']} in {aircraft['conflict_time_minutes_ahead']} min(s)")

        time.sleep(REPEAT_TIME)
