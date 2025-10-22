from utils.great_circle import is_point_on_path


def get_current_route_segment(waypoints, current_position):
    for i in range(len(waypoints)):
        current_waypoint = waypoints[i]
        next_waypoint = waypoints[i + 1] if i + 1 < len(waypoints) else None

        if next_waypoint is None:
            break

        result = is_point_on_path(current_waypoint[1], next_waypoint[1], current_position)
        if result is not None and result[0]:
            on_path, nm_dev = result
            return (current_waypoint, next_waypoint), nm_dev

    return None