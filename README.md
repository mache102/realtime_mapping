# Realtime 2D Mapping

Realtime 2D Mapping renders a live heatmap from position and scalar sensor
feeds. It subscribes to ROS 2 topic pairs (position + sensor), supports GPS
and local coordinate frames, and streams the result to an interactive
matplotlib window. A built-in **remote plot server** lets you view the same
heatmap on a phone or tablet browser over LAN. When no ROS hardware is
available, use `--dummy-data` to generate synthetic contour-like patterns.

## Key Features

- **Multi-input fusion** — subscribe to any number of position/sensor topic
  pairs defined in a shared YAML config.
- **Flexible message bindings** — reference nested fields with dot notation
  (`pose.pose.position.x`) or array indexing (`intensities[0]`).
- **Realtime heatmap** — configurable cell size, colormap, update rate, and
  aggregation policy (`latest`, `average`, `max`, `min`).
- **Remote plot** — stream the heatmap to a phone/tablet browser over LAN
  (FastAPI + WebSocket + Plotly.js with Griz-style UI).
- **Dummy data mode** — test everything end-to-end without ROS hardware.
- **Data export** — save CSV + PNG snapshots on demand or during shutdown.
- **Interactive tooling** — discover topics and generate configs with
  `topic_inspector`; replay synthetic data with `fake_publisher`.

---

## Setup (from scratch)

This section gets the backend mapper running locally. The remote plot
(phone viewer) is added in the next section.

### Prerequisites

- Python 3.8+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [`pnpm`](https://pnpm.io/) — `curl -fsSL https://get.pnpm.io/install.sh | sh -`

Setup ROS2
```bash
chmod +x ./ros2.sh

./ros2.sh
```



### 1. Clone and create the environment

```bash
git clone https://github.com/your-repo/realtime_mapping.git
cd realtime_mapping

# Create the venv inheriting the system-wide ROS 2 paths
uv venv --system-site-packages
source .venv/bin/activate

# Install project-specific dependencies (uv bridges to the system rclpy)
uv pip install numpy matplotlib PyYAML
```

### 2. Verify it works with dummy data

```bash

source .venv/bin/activate

cd realtime_mapping
python3 realtime_mapping/realtime_mapper.py --dummy-data
```

A matplotlib window opens showing a live heatmap with moving position
markers. Press `s` to save a CSV + PNG snapshot to `output/`. Press
`Ctrl+C` to stop.

### 3. (Optional) Use a real config instead of dummy data

```bash
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/gps_example.yaml
```

Or generate your own config interactively (requires ROS 2):

```bash
ros2 run realtime_mapping topic_inspector --interactive \
  --output realtime_mapping/config/generated_config.yaml
```

---

## Remote Plot — Phone / Tablet Viewer

Once the mapper runs locally, add remote plotting so you can watch the
heatmap from a phone or tablet on the same LAN.

### 1. Install extra Python dependencies

```bash
uv pip install fastapi uvicorn websockets
```

### 2. Build the frontend (one time)

```bash
cd remote-plot
pnpm install
pnpm build
cd ..
```

### 3. Run the mapper with remote plot

```bash
source .venv/bin/activate

# Dummy data (no ROS needed):
cd realtime_mapping
python3 realtime_mapping/realtime_mapper.py \
  --dummy-data \
  --remote-plot

# With a real config:
python3 realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/generated_config.yaml \
  --remote-plot
```

The terminal prints the LAN URL (e.g. `http://10.0.0.221:8090`).

If the phone cannot reach the laptop, allow the port:

```bash
sudo ufw allow 8090/tcp
```

### 4. (Optional) Reserve a static LAN IP

So the phone always reaches the same URL across sessions:

```bash
sudo ./scripts/setup_dhcp.sh
```

Troubleshooting: see [`scripts/dhcp_troubleshooting.md`](scripts/dhcp_troubleshooting.md).

### 5. On the phone / tablet

1. Connect to the **same LAN** as the laptop.
2. Open a web browser (Chrome recommended).
3. Enter the URL shown in the laptop terminal.
4. The page loads with:
   - **Plot** (top 50 %) — live-updating heatmap with position markers.
   - **Reconnect button** — tap to manually restart the WebSocket.
   - **Log area** (bottom) — connection status and errors.

---

## With ROS Hardware

If you have ROS 2 Humble (or newer) and live topic data, you can build the
package inside a colcon workspace and use `ros2 run`.

### Build

```bash
cd ~/ros2_ws/src
cp -r /path/to/realtime_mapping/realtime_mapping .

cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select realtime_mapping
source install/setup.bash
```

### Discover topics and craft a config

```bash
# List available topics with message types
ros2 run realtime_mapping topic_inspector --list

# Interactive selection — writes a template config
ros2 run realtime_mapping topic_inspector --interactive \
  --output config/generated_config.yaml
```

Merge the generated snippet into your config under the `inputs` array.

### Run

```bash
# Matplotlib window only
ros2 run realtime_mapping realtime_mapper \
  --config config/generated_config.yaml

# With remote plot for phone viewing
ros2 run realtime_mapping realtime_mapper \
  --config config/generated_config.yaml \
  --remote-plot
```

### Generate synthetic ROS data (for demos)

In a separate terminal:

```bash
ros2 run realtime_mapping fake_publisher --config config/message_config.yaml
```

The fake publisher reads the `inputs` list and publishes circular trajectories
with noisy sensor values for every entry where `simulation.enabled` is true.

### Launch file

```bash
ros2 launch realtime_mapping realtime_mapping_launch.py \
  config_file:=config/message_config.yaml \
  interactive:=false
```

---

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--config`, `-c` | `config/message_config.yaml` | Path to YAML config file |
| `--remote-plot` | *off* | Start the browser-accessible WebSocket server |
| `--remote-plot-port` | `8090` | Port for the remote server |
| `--dummy-data` | *off* | Generate synthetic contour-like data (no ROS needed) |
| `--interactive`, `-i` | *off* | Interactive topic selection |

---

## Configuration Reference

The mapper reads a YAML config. Example configs live in
`realtime_mapping/config/`.

### Full structure

```yaml
# Shared sensor value range for colormap scaling
sensor_defaults:
  value_range: { min: 0.0, max: 100.0 }

# Heatmap parameters
mapping:
  cell_size: 1.0
  map_size: { width: 100, height: 100 }
  origin: { x: 0.0, y: 0.0 }
  update_method: average          # latest | average | max | min
  display:
    colormap: viridis
    update_rate: 10.0
    show_colorbar: true

# Data export
output:
  csv:
    enabled: true
    filename_pattern: mapping_data_{timestamp}.csv
    include_metadata: true
  image:
    enabled: true
    filename_pattern: heatmap_{timestamp}.png
    format: png
    dpi: 300

# Input definitions (one or more)
inputs:
  - name: "example"
    position:
      topic: "/p1/pose2D"
      message_type: "geometry_msgs/msg/Pose2D"
      fields: { x: "x", y: "y" }
      # For Cartesian frames, optionally set an origin offset:
      # origin: { x: 0.0, y: 0.0 }
      #
      # For GPS (NavSatFix), use latitude/longitude and geo_origin:
      # fields:
      #   latitude: "latitude"
      #   longitude: "longitude"
      # geo_origin: { latitude: 37.0, longitude: -122.0 }
    sensor_data:
      topic: "/p1/rssi"
      message_type: "std_msgs/msg/Float64"
      fields: { value: "data" }
    # simulation hints (used by fake_publisher):
    # simulation:
    #   enabled: true
    #   motion: { radius: 5.0, rate: 5.0 }
```

### Key sections

| Section | Purpose |
|---------|---------|
| `sensor_defaults` | Value range (min/max) for colormap scaling |
| `mapping` | Cell size, map dimensions, origin, update policy, display options |
| `output` | CSV and image export settings |
| `inputs[]` | Position + sensor topic pairs with field mappings and optional GPS/Cartesian origin |

Nested ROS message fields use **dot notation** (`pose.pose.position.x`); array
elements use **bracket notation** (`intensities[0]`).

### Example presets

```bash
# GPS-only mapping
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/gps_example.yaml

# Robot pose + range sensor
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/robot_pose_example.yaml

# Odometry + range
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/odom_range_example.yaml
```

---

## Controlling the Visualiser

- Press **`s`** in the matplotlib window to save a CSV + PNG snapshot to
  `output/`.
- Close the window or press `Ctrl+C` to stop. Shutdown handlers persist
  data if export is enabled in the config.
- Enable verbose logging (ROS mode only):
  ```bash
  ros2 run realtime_mapping realtime_mapper --ros-args --log-level debug
  ```

---

## Repository Layout

```
realtime_mapping/
├── realtime_mapping/
│   ├── realtime_mapping/
│   │   ├── realtime_mapper.py         # main mapping node
│   │   ├── remote_plot_server.py      # FastAPI + WebSocket server
│   │   ├── dummy_data_generator.py    # offline synthetic data
│   │   ├── fake_publisher.py          # synthetic ROS publisher
│   │   └── topic_inspector.py         # topic discovery + config generator
│   ├── config/                        # YAML configs and example presets
│   ├── launch/                        # ROS 2 launch files
│   └── scripts/                       # helper scripts
├── remote-plot/                       # phone/tablet frontend
│   └── src/
│       ├── main.ts                    # WebSocket client + Plotly.js heatmap
│       ├── style.css                  # Griz-style layout overrides
│       └── reusable-ui-bundle.css     # Griz design system
├── scripts/
│   ├── setup_dhcp.sh                 # static LAN IP reservation
│   └── dhcp_troubleshooting.md        # network debugging guide
└── README.md                          # this file
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Phone can't reach laptop | Same LAN? Run `sudo ufw allow 8090/tcp` |
| Blank heatmap | Position topic must publish before sensor topic |
| `ModuleNotFoundError: rclpy` | ROS 2 not sourced; use `--dummy-data` to skip ROS |
| `ModuleNotFoundError: fastapi` | Run `uv pip install fastapi uvicorn websockets` |
| `remote-plot/dist` not found | Run `cd remote-plot && pnpm install && pnpm build` |
| GPS data plots in wrong spot | Verify `geo_origin` lat/lon in the config |
| Fake publisher idle | Set `simulation.enabled: true` for that input |
| No topics in inspector | Are ROS nodes running? Try `ros2 topic list` first |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## License

MIT — see [`LICENSE`](LICENSE) for details.
