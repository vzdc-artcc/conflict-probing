from config import VERTICAL_TOLERANCE_FT
from utils.collision_status import is_red_alert, is_yellow_alert
from utils.great_circle import haversine_distance


def get_collision_status(pos1, pos2):
    lat1, lon1, alt1, dev1 = pos1
    lat2, lon2, alt2, dev2 = pos2

    lateral_distance = haversine_distance(lat1, lon1, lat2, lon2) - dev1 - dev2
    vertical_distance = abs(alt1 - alt2) + VERTICAL_TOLERANCE_FT

    if is_red_alert(lateral_distance, vertical_distance):
        return 2
    elif is_yellow_alert(lateral_distance, vertical_distance):
        return 1
    else:
        return 0


def get_status_text(status):
    if status == 2:
        return "RED"
    elif status == 1:
        return "YELLOW"

    return None