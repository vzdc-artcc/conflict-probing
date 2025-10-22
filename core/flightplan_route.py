from utils.faa import deconstruct_awy, get_lat_lon


def route_to_lat_lon(route_str):
    waypoints = route_str.split(' ')
    waypoints = [wp.split('/')[0] for wp in waypoints if wp != 'DCT' and wp != '']

    coordinates = []
    for waypoint in waypoints:
        if is_airway_regex(waypoint):
            from_fix = waypoints[waypoints.index(waypoint) - 1] if waypoints.index(waypoint) > 0 else None
            to_fix = waypoints[waypoints.index(waypoint) + 1] if waypoints.index(waypoint) < len(
                waypoints) - 1 else None
            airway_points = deconstruct_awy(waypoint, from_fix, to_fix)
            for awy_wp in airway_points:
                awy_wp_coords = get_lat_lon(awy_wp)
                if awy_wp_coords:
                    coordinates.append((awy_wp, awy_wp_coords))

            continue

        waypoint_coordinates = get_lat_lon(waypoint)
        if waypoint_coordinates:
            coordinates.append((waypoint, waypoint_coordinates))

    return coordinates

def is_airway_regex(str):
    import re
    return bool(re.match(r"^[JVQT]\d{1,3}$", str))