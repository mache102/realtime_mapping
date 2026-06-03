"""Generate synthetic contour-like data for testing without ROS hardware.

Produces moving Gaussian blobs that simulate sensor readings
at the current position, creating interesting heatmap patterns.
"""

import math
import random
import time
import threading
from typing import Callable, Optional


class DummyDataGenerator:
    """Generates realistic contour-like heatmap data without ROS.

    Simulates an agent moving in a Lissajous-like pattern while
    depositing Gaussian-shaped sensor values onto the heatmap.
    """

    def __init__(
        self,
        map_width: int = 100,
        map_height: int = 100,
        cell_size: float = 1.0,
        origin_x: float = 0.0,
        origin_y: float = 0.0,
        update_rate: float = 10.0,
    ):
        self.map_width = map_width
        self.map_height = map_height
        self.cell_size = cell_size
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.update_rate = update_rate
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Lissajous parameters — tweaked to produce varied coverage
        self._phase = random.uniform(0, 2 * math.pi)
        self._ax = self.map_width * self.cell_size * 0.4
        self._ay = self.map_height * self.cell_size * 0.4
        self._wx = random.uniform(0.3, 0.7)
        self._wy = random.uniform(0.5, 1.1)
        self._t = 0.0

        # Gaussian blob width (in cells)
        self._sigma = random.uniform(3.0, 8.0)

        # Current sensor value drifts slowly
        self._base_value = random.uniform(20, 80)
        self._value_phase = random.uniform(0, 2 * math.pi)

    def _step(self) -> tuple:
        """Advance the simulation one step.

        Returns (x, y, value) for the current frame.
        """
        dt = 1.0 / self.update_rate
        self._t += dt * 0.5

        x = self._ax * math.sin(self._wx * self._t + self._phase)
        y = self._ay * math.cos(self._wy * self._t)

        # Drifting sensor value with some noise
        self._value_phase += dt * 0.3
        value = self._base_value + 25 * math.sin(self._value_phase)
        value += random.gauss(0, 3)
        value = max(0, min(100, value))

        return x, y, value

    def _deposit_gaussian(self, heatmap_values, heatmap_counts, cx, cy, value):
        """Deposit a Gaussian blob centered at (cx, cy) onto the heatmap."""
        sigma = self._sigma
        half_w = self.map_width // 2
        half_h = self.map_height // 2

        # Only iterate over cells within ~3 sigma of the center
        radius_cells = int(3 * sigma) + 1
        cell_cx = int(cx / self.cell_size) + half_w
        cell_cy = int(cy / self.cell_size) + half_h

        for dy in range(-radius_cells, radius_cells + 1):
            for dx in range(-radius_cells, radius_cells + 1):
                gx = cell_cx + dx
                gy = cell_cy + dy
                if 0 <= gx < self.map_width and 0 <= gy < self.map_height:
                    dist_sq = dx * dx + dy * dy
                    weight = math.exp(-dist_sq / (2 * sigma * sigma))
                    contrib = value * weight

                    old_count = heatmap_counts[gy, gx]
                    new_count = old_count + 1
                    if old_count == 0:
                        heatmap_values[gy, gx] = contrib
                    else:
                        heatmap_values[gy, gx] = (
                            heatmap_values[gy, gx] * old_count + contrib
                        ) / new_count
                    heatmap_counts[gy, gx] = new_count

    def start(
        self,
        heatmap_values,
        heatmap_counts,
        positions_dict: dict,
        lock: threading.Lock,
    ) -> None:
        """Start generating dummy data on a background thread."""
        self._running = True

        def _run():
            while self._running:
                x, y, value = self._step()

                with lock:
                    positions_dict["dummy"] = (x, y)
                    self._deposit_gaussian(
                        heatmap_values, heatmap_counts, x, y, value
                    )

                time.sleep(1.0 / self.update_rate)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the dummy data generator."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
