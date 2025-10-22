from config import LATERAL_SEPARATION_RED_NM, VERTICAL_SEPARATION_RED_FT, \
    LATERAL_SEPARATION_YELLOW_NM, VERTICAL_SEPARATION_YELLOW_FT


def check_below_threshold(threshold_lateral, threshold_vertical, lateral_distance, vertical_distance):
    return lateral_distance <= threshold_lateral and vertical_distance <= threshold_vertical


def is_red_alert(lateral_distance, vertical_distance):
    return check_below_threshold(LATERAL_SEPARATION_RED_NM, VERTICAL_SEPARATION_RED_FT, lateral_distance,
                                 vertical_distance)


def is_yellow_alert(lateral_distance, vertical_distance):
    return check_below_threshold(LATERAL_SEPARATION_YELLOW_NM, VERTICAL_SEPARATION_YELLOW_FT, lateral_distance,
                                 vertical_distance)
