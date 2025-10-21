red_lateral_threshold_nm = 5  # nautical miles
red_vertical_threshold_ft = 1000  # feet
yellow_lateral_threshold_nm = 12  # nautical miles
yellow_vertical_threshold_ft = 2000  # feet
v_tolerance = 100

def get_collision_status(lat1, lon1, alt1, dev1, lat2, lon2, alt2, dev2):
    from haversine import haversine_distance

    # Calculate horizontal distance in nautical miles
    horizontal_distance = haversine_distance(lat1, lon1, lat2, lon2) - dev1 - dev2

    # Calculate vertical distance in feet
    vertical_distance = abs(alt1 - alt2) + v_tolerance

    # Determine collision status
    if horizontal_distance <= red_lateral_threshold_nm and vertical_distance <= red_vertical_threshold_ft:
        return 2  # red alert
    elif horizontal_distance <= yellow_lateral_threshold_nm and vertical_distance <= yellow_vertical_threshold_ft:
        return 1  # yellow alert
    else:
        return 0  # No collision

def get_status_info(status):
    if status == 2:
        return "RED"
    elif status == 1:
        return "YELLOW"
    else:
        return "N/A"