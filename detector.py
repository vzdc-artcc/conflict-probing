# python
import time
from itertools import combinations

from collision import get_collision_status, get_status_info
from next_waypoint import point_within_gc_arc_tol
from route_parser import get_coords_from_route
from vatsim import fetch_vatsim_data
from typing import List, Tuple, Optional, Any, Dict

bottom_left_limit = (32, -130)  # (lat, lon)
top_right_limit = (48, -62.6)    # (lat, lon)
altitude_limit = 180 * 100
tolerance_nm = 4
pred_mins_ahead = 10
pred_mins_precision = 1

# collision thresholds
HORIZONTAL_SEP_NM = 5.0
VERTICAL_SEP_FT = 1000.0


def locate_current_segment(waypoints: List[Tuple[str, Tuple[float, float]]],
                           ac_lat_long: Tuple[float, float],
                           tolerance_nm: float) -> Optional[Tuple[Tuple[Any, Any], float]]:
    i = 0
    while i in range(len(waypoints)):
        waypoint = (waypoints[i][1][0], waypoints[i][1][1])
        if i + 1 < len(waypoints):
            waypoint_next = (waypoints[i + 1][1][0], waypoints[i + 1][1][1])
        else:
            break

        result = point_within_gc_arc_tol(waypoint, waypoint_next, ac_lat_long, tolerance_nm)
        if result is None:
            i += 1
            continue

        on_path, nm_dist = result
        if on_path:
            return (waypoints[i], waypoints[i + 1]), nm_dist

        i += 1

    return None


def get_airplanes_segments(bottom_left, top_right, altitude_limit, tolerance_nm) -> List[Tuple[Any, float, dict, List]]:
    airplanes = fetch_vatsim_data(bottom_left, top_right, altitude_limit)
    airplanes_segments = []

    print(f"Processing {len(airplanes)} airplane(s)")
    for airplane in airplanes:
        # print(f"Processing airplane: {airplane.get('callsign')}")
        ac_lat_long = (airplane['latitude'], airplane['longitude'])

        # build route string; skip if no route/origin/destination info
        if not any([airplane.get('origin'), airplane.get('route'), airplane.get('destination')]):
            continue
        route = f"{airplane.get('origin') or ''} {airplane.get('route') or ''} {airplane.get('destination') or ''}"

        waypoints = get_coords_from_route(route)
        if not waypoints:
            continue

        seg = locate_current_segment(waypoints, ac_lat_long, tolerance_nm)
        if seg:
            current_segment, current_segment_deviation_nm = seg
            airplanes_segments.append((current_segment, current_segment_deviation_nm, airplane, waypoints))

    return airplanes_segments


def filter_airplanes_segments(airplanes_segments: List[Tuple[Any, float, dict, List]]):
    filtered = []
    for current_segment, current_segment_deviation_nm, airplane, waypoints in airplanes_segments:
        origin = (airplane.get('origin') or '').upper()
        destination = (airplane.get('destination') or '').upper()

        wp1_name = (current_segment[0][0] or '').upper()
        wp2_name = (current_segment[1][0] or '').upper()

        if wp1_name == origin or wp2_name == destination:
            continue

        filtered.append((current_segment, current_segment_deviation_nm, airplane, waypoints))
    return filtered


def predict_for_segments(segments: List[Tuple[Any, float, dict, List]], pred_mins_ahead: int) -> List[Dict]:
    from path_prediction import predict_lat_long_alt

    predictions: List[Dict] = []

    for current_segment, current_segment_deviation_nm, airplane, waypoints in segments:
        callsign = airplane.get('callsign')

        ac_lat_long = (airplane['latitude'], airplane['longitude'])
        ac_alt = airplane['altitude']
        ac_vs = airplane['vertical_speed']
        ac_gs = airplane['ground_speed']
        ac_trk = airplane['heading']

        cruise_alt = airplane.get('cruising_altitude')
        if isinstance(cruise_alt, int) or (isinstance(cruise_alt, str) and cruise_alt.isdigit()):
            cruise_alt_int = int(cruise_alt)
        else:
            cruise_alt_int = None

        result = predict_lat_long_alt(
            ac_lat_long[0],
            ac_lat_long[1],
            ac_alt,
            ac_vs,
            ac_gs,
            ac_trk,
            current_segment[1],
            waypoints,
            cruise_alt_int,
            pred_mins_ahead
        )

        entry: Dict = {
            "callsign": callsign,
            "minutes_ahead": pred_mins_ahead,
            "current": {"lat": ac_lat_long[0], "lon": ac_lat_long[1], "alt": ac_alt},
            "predicted": None,
            "status": "ok"
        }

        if result is None:
            entry["status"] = "insufficient_waypoint_data"
            predictions.append(entry)
            continue

        pred_lat, pred_long, pred_alt = result

        if pred_lat is not None and pred_long is not None and pred_alt is not None:
            entry["predicted"] = {"lat": pred_lat, "lon": pred_long, "alt": pred_alt, "dev_nm": current_segment_deviation_nm}
        else:
            entry["status"] = "insufficient_waypoint_data"

        predictions.append(entry)

    return predictions


def evaluate_conflicts(predictions: List[Dict]):
    """
    Compare every prediction pair for the same minutes_ahead.
    Returns:
      - pairs: list of pairwise check dicts
      - status_map: dict mapping callsign -> {"status": 0|1|2, "minutes": [minutes...]}
    Severity:
      2 = both horizontal and vertical thresholds breached (collision)
      1 = either horizontal OR vertical threshold breached (separation issue)
      0 = no breach
    """
    pairs = []
    status_map: Dict[str, Dict] = {}

    n = len(predictions)
    for i in range(n):
        pi = predictions[i]
        for j in range(i + 1, n):
            pj = predictions[j]

            # require predicted positions and same minutes_ahead
            if not pi.get("predicted") or not pj.get("predicted"):
                continue
            if pi["minutes_ahead"] != pj["minutes_ahead"]:
                continue
            if pi["callsign"] == pj["callsign"]:
                continue

            p1 = pi["predicted"]
            p2 = pj["predicted"]

            severity = get_collision_status(p1['lat'], p1['lon'], p1['alt'], p1['dev_nm'], p2['lat'], p2['lon'], p2['alt'], p2['dev_nm'])

            pair_entry = {
                "callsign_a": pi["callsign"],
                "callsign_b": pj["callsign"],
                "minutes_ahead": pi["minutes_ahead"],
                "severity": severity
            }
            pairs.append(pair_entry)

            # update status_map for both callsigns
            for callsign in (pi["callsign"], pj["callsign"]):
                ent = status_map.setdefault(callsign, {"status": 0, "minutes": set()})
                # escalate status if needed
                if severity > ent["status"]:
                    ent["status"] = severity
                # record minutes if severity is 1 or 2
                if severity >= 1:
                    ent["minutes"].add(pi["minutes_ahead"])

    # normalize minutes sets to sorted lists
    for callsign, ent in status_map.items():
        ent["minutes"] = sorted(ent["minutes"])

    return pairs, status_map


def main() -> Dict[str, Any]:
    airplanes_segments = get_airplanes_segments(bottom_left_limit, top_right_limit, altitude_limit, tolerance_nm)

    filtered = filter_airplanes_segments(airplanes_segments)

    all_predictions: List[Dict] = []
    all_pairs: List[Dict] = []
    aggregate_statuses: Dict[str, Dict] = {}

    minutes = pred_mins_precision

    while minutes < pred_mins_ahead:
        # print(f"Predicting for {minutes} minutes ahead:")
        preds = predict_for_segments(filtered, minutes)

        # evaluate pairwise checks for this minute
        pairs, status_map = evaluate_conflicts(preds)

        # attach reduced status to each prediction (0/1/2) and minutes list if present
        for p in preds:
            sc = status_map.get(p["callsign"])
            if sc:
                p["reduced_status"] = sc["status"]
                p["status_minutes"] = sc["minutes"]
            else:
                p["reduced_status"] = 0
                p["status_minutes"] = []

        # aggregate pairs and statuses across minutes
        all_predictions.extend(preds)
        all_pairs.extend(pairs)

        for csign, info in status_map.items():
            agg = aggregate_statuses.setdefault(csign, {"status": 0, "minutes": set()})
            if info["status"] > agg["status"]:
                agg["status"] = info["status"]
            if info["status"] >= 1:
                agg["minutes"].update(info["minutes"])

        minutes += pred_mins_precision

    # normalize aggregate minutes sets to sorted lists
    for callsign, ent in aggregate_statuses.items():
        ent["minutes"] = sorted(ent["minutes"])

    return {
        "predictions": all_predictions,
        "pairs": all_pairs,
        "statuses": aggregate_statuses
    }

def group_conflict_pairs(predictions):
    """
    Returns a list of dicts for each pair in yellow or red status.
    Each dict contains: callsign1, callsign2, status, status_info
    """
    conflict_pairs = []
    for ac1, ac2 in combinations(predictions, 2):
        # Skip if predicted data is missing
        if not ac1.get('predicted') or not ac2.get('predicted'):
            continue
        status = get_collision_status(
            ac1['predicted']['lat'], ac1['predicted']['lon'], ac1['predicted']['alt'], ac1['predicted'].get('dev_nm', 0),
            ac2['predicted']['lat'], ac2['predicted']['lon'], ac2['predicted']['alt'], ac2['predicted'].get('dev_nm', 0)
        )
        if status >= 1:
            conflict_pairs.append({
                "callsign1": ac1['callsign'],
                "callsign2": ac2['callsign'],
                "status": status,
                "status_info": get_status_info(status)
            })
    return conflict_pairs

if __name__ == '__main__':
    print("Running with settings:")
    print(f"  Bottom-left limit (lat/lon): {bottom_left_limit}")
    print(f"  Top-right limit (lat/lon): {top_right_limit}")
    print(f"  Altitude floor: {altitude_limit} ft")
    print(f"  Lateral Tolerance: {tolerance_nm} nm")
    print(f"  Prediction range: {pred_mins_ahead} min")
    print(f"  Prediction precision: {pred_mins_precision} min")
    print()
    while True:
        results = main()
        print()
        print(f"Collected {len(results['predictions'])} predictions")
        print(f"Collected {len(results['pairs'])} pairwise checks")
        print()
        if all(info["status"] == 0 for info in results["statuses"].values()):
            print("No conflicts detected!")
        else:
            seen = set()
            unique_conflict_pairs = []
            for pair in group_conflict_pairs(results['predictions']):
                if pair['status'] > 0 and pair['callsign1'] != pair['callsign2']:
                    key = tuple(sorted([pair['callsign1'], pair['callsign2']]))
                    if key not in seen:
                        seen.add(key)
                        unique_conflict_pairs.append(pair)

            print("Conflicts:")
            for pair in unique_conflict_pairs:
                print(f"  {pair['callsign1']} <-> {pair['callsign2']}: {pair['status_info']}")
        time.sleep(60)