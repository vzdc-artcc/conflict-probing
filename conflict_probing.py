import time

from config import PREDICTION_MINUTES_AHEAD, PREDICTION_PRECISION_MINUTES
from core.collision import get_collision_status, get_status_text
from core.position_prediction import predict_lat_long_alt
from core.route_segment import get_current_route_segment
from core.vatsim_data_fetch import fetch_vatsim_data


def get_aircraft_conflict_status():
    data = fetch_vatsim_data()

    steps = max(1, int(PREDICTION_MINUTES_AHEAD / PREDICTION_PRECISION_MINUTES) + 1)
    for aircraft in data:
        from core.flightplan_route import route_to_lat_lon
        departure = aircraft.get('departure', '')
        arrival = aircraft.get('arrival', '')
        route = aircraft.get('route', '')
        lat_lon_coords = route_to_lat_lon(f"{departure} {route} {arrival}")
        aircraft['route_lat_lon'] = lat_lon_coords

        aircraft['p_steps'] = [{'latitude': None, 'longitude': None, 'altitude': None} for _ in range(steps)]

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

    data = [
        ac for ac in data
        if ac['current_route_segment'] is not None
           and ac['current_route_segment'][0] is not None
           and ac['current_route_segment'][1] is not None
           and ac['current_route_segment'][0] != ac['current_route_segment'][1]
           and ac['current_route_segment'][0] != ac['departure']
           and ac['current_route_segment'][1] != ac['arrival']
    ]
    conflicts = {}

    i = 0
    j = 0
    while i <= PREDICTION_MINUTES_AHEAD:
        temp_aircraft = []
        for ac in data:
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

            lat, lon, alt = predict_lat_long_alt(lat, lon, alt, vs, gs, trk, next_waypoint, all_waypoints, cruise_alt,
                                                 i)

            if lat is None or lon is None or alt is None:
                continue

            ac['p_steps'][j]['mins'] = i
            ac['p_steps'][j]['latitude'] = lat
            ac['p_steps'][j]['longitude'] = lon
            ac['p_steps'][j]['altitude'] = alt

            ac['p_latitude'] = lat
            ac['p_longitude'] = lon
            ac['p_altitude'] = alt
            temp_aircraft.append(ac)

        for idx, ac in enumerate(temp_aircraft):
            for jdx, ac2 in enumerate(temp_aircraft):
                if idx == jdx:
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

                if collision_status <= 0:
                    continue

                def consider_conflict(subject_ac, other_ac, severity, minute):
                    cs = subject_ac['callsign']
                    entry_time = minute
                    existing = conflicts.get(cs)

                    if existing is None or severity > existing['severity'] or (
                            severity == existing['severity'] and entry_time < existing['time']):
                        ac_copy = dict(subject_ac)
                        ac_copy['conflicting_callsign'] = other_ac['callsign']
                        ac_copy['conflict_time_minutes_ahead'] = minute
                        ac_copy['conflict_level'] = get_status_text(severity)
                        conflicts[cs] = {
                            'severity': severity,
                            'time': entry_time,
                            'conflicting_callsign': other_ac['callsign'],
                            'conflict_level': ac_copy['conflict_level'],
                            'ac': ac_copy
                        }

                consider_conflict(ac, ac2, collision_status, i)
                consider_conflict(ac2, ac, collision_status, i)

        i += PREDICTION_PRECISION_MINUTES
        j = j + 1

    conflicting_aircraft = [info['ac'] for info in conflicts.values()]
    conflicting_callsigns = set(conflicts.keys())

    non_conflicting_aircraft = []
    non_conflicting_callsigns = set()
    for ac in data:
        if ac['callsign'] in conflicting_callsigns:
            continue
        if 'p_latitude' in ac and ac['callsign'] not in non_conflicting_callsigns:
            non_conflicting_aircraft.append(ac)
            non_conflicting_callsigns.add(ac['callsign'])

    return conflicting_aircraft, non_conflicting_aircraft, time.time()