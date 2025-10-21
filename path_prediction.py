import numpy as np

from haversine import haversine_distance


def find_next_waypoints(next_waypoint, all_waypoints):
    for i in range(len(all_waypoints)):
        wp_name = all_waypoints[i][0]
        if wp_name == next_waypoint[0]:
            return all_waypoints[i:]
    return None



# great circle destination point given start point, bearing, and distance
def great_circle_destination(lat, lon, bearing, distance_nm):
    R = 3440.065  # Radius of the Earth in nautical miles
    bearing_rad = np.radians(bearing)
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    distance_rad = distance_nm / R

    new_lat_rad = np.arcsin(np.sin(lat_rad) * np.cos(distance_rad) +
                            np.cos(lat_rad) * np.sin(distance_rad) * np.cos(bearing_rad))

    new_lon_rad = lon_rad + np.arctan2(np.sin(bearing_rad) * np.sin(distance_rad) * np.cos(lat_rad),
                                       np.cos(distance_rad) - np.sin(lat_rad) * np.sin(new_lat_rad))

    new_lat = np.degrees(new_lat_rad)
    new_lon = np.degrees(new_lon_rad)

    return new_lat, new_lon

def predict_lat_long_alt(lat, long, alt, vs, gs, trk, next_waypoint, waypoints, crz, mins):
    # print(next_waypoint)
    next_waypoints = find_next_waypoints(next_waypoint, waypoints)

    if not next_waypoints:
        return None, None, None

    if -150 <= vs <= 150:
        vs = 0

    pred_alt = alt + (vs * mins)

    if crz is not None:
        if (vs < 0 and pred_alt < crz) or (vs > 0 and pred_alt > crz):
            pred_alt = crz

    pred_distance_covered_nm = (gs * mins) / 60

    distance_to_next_wp_nm = haversine_distance(lat, long, next_waypoints[0][1][0], next_waypoints[0][1][1])
    distance_remaining = pred_distance_covered_nm - distance_to_next_wp_nm

    # print(next_waypoints)
    if distance_remaining < 0:
        pred_lat, pred_long = great_circle_destination(lat, long, trk, pred_distance_covered_nm)
        return pred_lat, pred_long, pred_alt
    else:
        i = 0

        lat = next_waypoints[0][1][0]
        long = next_waypoints[0][1][1]
        while i + 1 < len(next_waypoints):
            i += 1
            waypoint = next_waypoints[i]
            # print(waypoint)
            distance = haversine_distance(lat, long, waypoint[1][0], waypoint[1][1])
            old_distance_remaining = distance_remaining
            distance_remaining = distance_remaining - distance
            # print(distance_remaining)
            if distance_remaining < 0:
                #get track from prev to waypoint
                new_trk = np.degrees(np.arctan2(
                    np.radians(waypoint[1][1] - long) * np.cos(np.radians((lat + waypoint[1][0]) / 2)),
                    np.radians(waypoint[1][0] - lat)
                ))
                pred_lat, pred_long = great_circle_destination(lat, long, new_trk, old_distance_remaining)
                return pred_lat, pred_long, pred_alt
            elif distance_remaining == 0:
                return lat, long, pred_alt

            i += 1
            if i >= len(next_waypoints):
                break

            waypoint = next_waypoints[i]
            lat = waypoint[1][0]
            long = waypoint[1][1]
        return None



