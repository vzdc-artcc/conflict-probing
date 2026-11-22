import json
import importlib.util
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import vertical_speed


class VerticalSpeedHistoryTests(unittest.TestCase):
    def test_discards_entries_older_than_calculation_window(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "vertical-speed.json"
            now = time.time()
            cache_path.write_text(json.dumps({
                "STALE": {"altitude": 30000, "timestamp": now - 601},
                "CURRENT": {"altitude": 30000, "timestamp": now - 10},
            }))

            with patch.object(vertical_speed, "VERTICAL_SPEED_CACHE_FILE", str(cache_path)):
                aircraft = [
                    {"callsign": "CURRENT", "altitude": 30100},
                    {"callsign": "NEW", "altitude": 32000},
                ]
                vertical_speed.batch_compute_vertical_speed(aircraft)

            saved_data = json.loads(cache_path.read_text())
            self.assertNotIn("STALE", saved_data)
            self.assertIn("CURRENT", saved_data)
            self.assertIn("NEW", saved_data)
            self.assertNotEqual(aircraft[0]["vertical_speed"], 0)


@unittest.skipUnless(
    importlib.util.find_spec("fastapi"),
    "FastAPI is required to exercise api.update_cache",
)
class CacheRefreshLockTests(unittest.TestCase):
    def test_skips_overlapping_refreshes(self):
        import api

        calls = 0

        def refresh():
            nonlocal calls
            calls += 1
            time.sleep(0.05)
            return [], [], time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(api, "get_aircraft_conflict_status", side_effect=refresh), \
                    patch.object(api, "DATA_CACHE_FILE", str(Path(temp_dir) / "cache.json")):
                first = threading.Thread(target=api.update_cache)
                second = threading.Thread(target=api.update_cache)
                first.start()
                second.start()
                first.join()
                second.join()

        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
