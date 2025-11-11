from utils.faa import deconstruct_awy, get_lat_lon, deconstruct_procedure


def route_to_lat_lon(route_str):
    waypoints = route_str.split(' ')
    waypoints = [wp.split('/')[0] for wp in waypoints if wp != 'DCT' and wp != '']

    coordinates = []
    for waypoint in waypoints:
        if is_procedure_regex(waypoint):
            transition = waypoints[waypoints.index(waypoint) + 1] if waypoints.index(waypoint) == 1 and waypoints.index(waypoint) + 1 < len(waypoints) else None
            if waypoints.index(waypoint) == len(waypoints) - 2:
                if len(waypoints) >= 2:
                    transition = waypoints[len(waypoints) - 3]

            procedure_points = deconstruct_procedure(waypoint, transition)
            for proc_wp in procedure_points:
                proc_wp_coords = get_lat_lon(proc_wp)
                if proc_wp_coords:
                    lat, lon = proc_wp_coords
                    coordinates.append({
                        'name': proc_wp,
                        'latitude': lat,
                        'longitude': lon
                    })

            continue

        if is_airway_regex(waypoint):
            from_fix = waypoints[waypoints.index(waypoint) - 1] if waypoints.index(waypoint) > 0 else None
            to_fix = waypoints[waypoints.index(waypoint) + 1] if waypoints.index(waypoint) < len(
                waypoints) - 1 else None
            airway_points = deconstruct_awy(waypoint, from_fix, to_fix)
            for awy_wp in airway_points:
                awy_wp_coords = get_lat_lon(awy_wp)
                if awy_wp_coords:
                    lat, lon = awy_wp_coords
                    coordinates.append({
                        'name': awy_wp,
                        'latitude': lat,
                        'longitude': lon
                    })

            continue

        waypoint_coordinates = get_lat_lon(waypoint)
        if waypoint_coordinates:
            lat, lon = waypoint_coordinates
            coordinates.append({
                'name': waypoint,
                'latitude': lat,
                'longitude': lon
            })

    return coordinates


def is_airway_regex(str):
    import re
    return bool(re.match(r"^[JVQT]\d{1,3}$", str))

def is_procedure_regex(str):
    import re
    return bool(re.match(r"^[A-Z]{3,5}\d$", str))