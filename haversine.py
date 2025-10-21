# great circle distance in nautical miles
import numpy as np


def haversine_distance(lat1, lon1, lat2, lon2):
    # print("Calculating haversine distance between ({}, {}) and ({}, {})".format(lat1, lon1, lat2, lon2))
    R = 3440.065  # Radius of the Earth in nautical miles
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + \
        np.cos(phi1) * np.cos(phi2) * \
        np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c