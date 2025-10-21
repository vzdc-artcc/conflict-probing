import re
from nasr import get_awy_points, get_lat_lon

def get_coords_from_route(route):
    waypoints = route.split(' ')
    waypoints = [wp.split('/')[0] for wp in waypoints if wp != 'DCT' and wp != '']


    coords = []
    for waypoint in waypoints:
        if is_airway(waypoint):
            from_fix = waypoints[waypoints.index(waypoint) - 1] if waypoints.index(waypoint) > 0 else None
            to_fix = waypoints[waypoints.index(waypoint) + 1] if waypoints.index(waypoint) < len(waypoints) - 1 else None
            airway_points = get_awy_points(waypoint, from_fix, to_fix)
            if airway_points:
                for awy_wp in airway_points:
                    awy_wp_coords = get_lat_lon(awy_wp)
                    if awy_wp_coords:
                        coords.append((awy_wp, awy_wp_coords))
        else:
            waypoint_coords = get_lat_lon(waypoint)
            if waypoint_coords:
                coords.append((waypoint, waypoint_coords))

    return coords

def is_airway(token):
    return bool(re.match(r"^[JVQT]\d{1,3}$", token.upper()))