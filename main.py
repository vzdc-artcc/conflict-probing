import time

from config import print_config_vars, PREDICTION_PRECISION_MINUTES, PREDICTION_MINUTES_AHEAD, REPEAT_TIME
from core.collision import get_collision_status, get_status_text
from core.position_prediction import predict_lat_long_alt
from core.route_segment import get_current_route_segment
from core.vatsim_data_fetch import fetch_vatsim_data


def get_aircraft_conflict_status():
    # print("Fetching data from VATSIM...")
    data = fetch_vatsim_data()
    # print(f"Successfully fetched {len(data)} airplane(s) from VATSIM within lat/lon and altitude limits.")
    # print()
    # print("Converting aircraft routes to lat/lon coordinates...")

    for aircraft in data:
        from core.flightplan_route import route_to_lat_lon
        departure = aircraft.get('departure', '')
        arrival = aircraft.get('arrival', '')
        route = aircraft.get('route', '')
        lat_lon_coords = route_to_lat_lon(f"{departure} {route} {arrival}")
        aircraft['route_lat_lon'] = lat_lon_coords

    # print("Successfully converted all aircraft routes to lat/lon coordinates.")
    # print()
    # print("Computing current route segment for all aircraft...")

    for aircraft in data:
        result = get_current_route_segment(aircraft['route_lat_lon'],
                                                    (aircraft['latitude'], aircraft['longitude']))

        if result is None:
            aircraft['current_route_segment'] = None
            aircraft['current_route_segment_nm_deviation'] = None
            continue

        segment, nm_dev = result
        aircraft['current_route_segment'] = segment
        aircraft['current_route_segment_nm_deviation'] = nm_dev

    # print("Successfully computed current route segment for all aircraft.")
    # print()
    # print(
    #     "Filtering out all aircraft that are not on a route segment or are transitioning from origin or arriving to destination...")
    # print("(SID and STAR logic will be implemented later)")
    # print()
    data = [
        ac for ac in data
        if ac['current_route_segment'] is not None
           and ac['current_route_segment'][0] is not None
           and ac['current_route_segment'][1] is not None
           and ac['current_route_segment'][0] != ac['current_route_segment'][1]
           and ac['current_route_segment'][0] != ac['departure']
           and ac['current_route_segment'][1] != ac['arrival']
    ]
    # print(f"{len(data)} aircraft remain after filtering.")
    # print()
    # print("Computing predicted position and conflicts for all aircraft (This will take some time)...")
    conflicting_aircraft = []
    conflicting_callsigns = set()
    non_conflicting_aircraft = []
    non_conflicting_aircraft_callsigns = set()
    i = 0
    while i <= PREDICTION_MINUTES_AHEAD:
        temp_aircraft = []
        for ac in data:
            if ac['callsign'] in conflicting_callsigns:
                temp_aircraft.append(ac)
                continue

            lat = ac['latitude']
            lon = ac['longitude']
            alt = ac['altitude']
            vs = ac['vertical_speed']
            gs = ac['ground_speed']
            trk = ac['heading']
            cruise_alt = ac['cruising_altitude']

            segment = ac['current_route_segment']
            next_waypoint = segment[1]
            all_waypoints = ac['route_lat_lon']

            lat, lon, alt = predict_lat_long_alt(lat, lon, alt, vs, gs, trk, next_waypoint, all_waypoints, cruise_alt, i)

            if lat is None or lon is None or alt is None:
                continue

            ac['p_latitude'] = lat
            ac['p_longitude'] = lon
            ac['p_altitude'] = alt
            temp_aircraft.append(ac)

        for ac in temp_aircraft:
            if ac['callsign'] in conflicting_callsigns:
                continue
            for ac2 in temp_aircraft:
                if ac2['callsign'] == ac['callsign']:
                    continue

                ac_lat = ac['p_latitude']
                ac_lon = ac['p_longitude']
                ac_alt = ac['p_altitude']
                ac_dev = ac['current_route_segment_nm_deviation']

                ac2_lat = ac2['p_latitude']
                ac2_lon = ac2['p_longitude']
                ac2_alt = ac2['p_altitude']
                ac2_dev = ac2['current_route_segment_nm_deviation']

                collision_status = get_collision_status(
                    (ac_lat, ac_lon, ac_alt, ac_dev),
                    (ac2_lat, ac2_lon, ac2_alt, ac2_dev)
                )

                ac['conflict_status'] = collision_status

                if collision_status > 0:
                    ac['conflicting_callsign'] = ac2['callsign']
                    ac['conflict_time_minutes_ahead'] = i
                    ac['conflict_level'] = get_status_text(collision_status)
                    conflicting_aircraft.append(ac)
                    conflicting_callsigns.add(ac['callsign'])
                    conflicting_callsigns.add(ac2['callsign'])

            if ac['callsign'] not in conflicting_callsigns and ac['callsign'] not in non_conflicting_aircraft_callsigns:
                non_conflicting_aircraft.append(ac)
                non_conflicting_aircraft_callsigns.add(ac['callsign'])

        i += PREDICTION_PRECISION_MINUTES

    # print("Successfully computed predicted position and conflicts for all aircraft.")
    return conflicting_aircraft, non_conflicting_aircraft, time.time()


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
        # print()
        # print()
        # print(f"Total aircraft: {len(conflicting) + len(non_conflicting)}")
        # print(f"Conflicting aircraft: {len(conflicting)}")
        # print(f"Non-conflicting aircraft: {len(non_conflicting)}")
        # print(f"Execution time: {time.time() - start:.2f} seconds")
        # print()
        if len(conflicting) == 0:
            print("No alerts detected!")
        else:
            for aircraft in conflicting:
                print(f"{aircraft['callsign']} <-> {aircraft['conflicting_callsign']}: {aircraft['conflict_level']} in {aircraft['conflict_time_minutes_ahead']} min(s)")

        time.sleep(REPEAT_TIME)
