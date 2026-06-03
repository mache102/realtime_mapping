# Realtime Mapping Workspace

Realtime 2D sensor mapping with heatmap visualization — viewable on a phone
or tablet browser over LAN. Subscribes to ROS 2 position + sensor topics and
renders a live heatmap. Also works **without ROS hardware** via built-in
dummy data generation.

---

## Quick Start (no ROS, no hardware — dummy data)

```bash
# 1. Clone and enter the repo
git clone https://github.com/your-repo/realtime_mapping.git
cd realtime_mapping

# 2. Create a Python virtual environment with uv
uv venv
source .venv/bin/activate

# 3. Install Python dependencies
uv pip install numpy matplotlib PyYAML fastapi uvicorn websockets

# 4. Build the phone/tablet frontend (one time)
cd remote-plot
pnpm install
pnpm build
cd ..

# 5. Run the mapper with dummy data + remote plot
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --dummy-data \
  --remote-plot
```

The terminal prints the LAN URL (e.g. `http://10.0.0.221:8090`). Open it on
your phone or tablet to see the live heatmap.

---

## Remote Plot (Phone / Tablet Viewer)

The remote plot streams the live heatmap to any browser on the same LAN. The
laptop runs a **FastAPI + WebSocket** server; the phone loads a **Plotly.js**
frontend styled with the Griz design system.

### Laptop — one-time setup

```bash
# Python environment (skip if done above)
uv venv && source .venv/bin/activate
uv pip install numpy matplotlib PyYAML fastapi uvicorn websockets

# Frontend build (skip if done above)
cd remote-plot && pnpm install && pnpm build && cd ..
```

### Laptop — run the mapper

```bash
source .venv/bin/activate

# With ROS hardware:
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/generated_config.yaml \
  --remote-plot

# Without ROS hardware (dummy data):
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --dummy-data \
  --remote-plot
```

The terminal prints a LAN URL. If the port is blocked by a firewall, run:

```bash
sudo ufw allow 8090/tcp
```

### (Optional) Reserve a static LAN IP

So the phone always reaches the same URL:

```bash
sudo ./scripts/setup_dhcp.sh
```

Troubleshooting: see [`scripts/dhcp_troubleshooting.md`](scripts/dhcp_troubleshooting.md).

### Phone / Tablet

1. Connect to the **same LAN** as the laptop.
2. Open a web browser (Chrome recommended).
3. Enter the URL shown in the laptop terminal.
4. The page loads with:
   - **Plot** (top 50 %) — live-updating heatmap with position markers.
   - **Reconnect button** — tap to manually restart the WebSocket.
   - **Log area** (bottom) — connection status and errors.

---

## With ROS Hardware

If you have ROS 2 installed and want live topic data:

### Prerequisites

- ROS 2 Humble (or newer)
- A running ROS system publishing position + sensor topics

### Build (inside a ROS workspace)

```bash
cd ~/ros2_ws/src
cp -r /path/to/realtime_mapping/realtime_mapping .

cd ~/ros2_ws
colcon build --packages-select realtime_mapping
source install/setup.bash
```

### Discover topics and generate a config

```bash
# Interactively pick topics
ros2 run realtime_mapping topic_inspector --interactive \
  --output realtime_mapping/config/generated_config.yaml
```

### Run the mapper

```bash
# With matplotlib window only
ros2 run realtime_mapping realtime_mapper \
  --config config/generated_config.yaml

# With remote plot for phone viewing
ros2 run realtime_mapping realtime_mapper \
  --config config/generated_config.yaml \
  --remote-plot
```

Press `s` in the matplotlib window to save a CSV + PNG snapshot to `output/`.

---

## CLI Flags

| Flag | Description |
|------|-------------|
| `--config`, `-c` | Path to YAML config file |
| `--remote-plot` | Start the browser-accessible WebSocket server |
| `--remote-plot-port` | Port for the remote server (default: `8090`) |
| `--dummy-data` | Generate synthetic contour-like data (no ROS needed) |
| `--interactive`, `-i` | Interactive topic selection |

---

## Configuration

The mapper reads a YAML config file. See `realtime_mapping/config/` for
examples.

Minimal structure:

```yaml
mapping:
  cell_size: 1.0
  map_size: { width: 100, height: 100 }
  origin: { x: 0.0, y: 0.0 }
  update_method: average
  display:
    colormap: viridis
    update_rate: 10.0
    show_colorbar: true

output:
  csv:  { enabled: true }
  image: { enabled: true, dpi: 300, format: png }

inputs:
  - name: "example"
    position:
      topic: "/p1/pose2D"
      message_type: "geometry_msgs/msg/Pose2D"
      fields: { x: "x", y: "y" }
    sensor_data:
      topic: "/p1/rssi"
      message_type: "std_msgs/msg/Float64"
      fields: { value: "data" }
```

Nested message fields use dot notation (`pose.pose.position.x`); array
elements use bracket notation (`intensities[0]`).

Example configs to run directly:

```bash
python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/gps_example.yaml

python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/robot_pose_example.yaml

python3 realtime_mapping/realtime_mapping/realtime_mapper.py \
  --config realtime_mapping/config/odom_range_example.yaml
```

---

## Repository Layout

```
realtime_mapping/
├── realtime_mapping/
│   ├── realtime_mapping/
│   │   ├── realtime_mapper.py         # main mapping node
│   │   ├── remote_plot_server.py      # FastAPI + WebSocket server
│   │   ├── dummy_data_generator.py    # synthetic data for offline testing
│   │   ├── fake_publisher.py          # synthetic ROS publisher
│   │   └── topic_inspector.py         # topic discovery + config generator
│   ├── config/                        # YAML configs and examples
│   ├── launch/                        # ROS 2 launch files
│   └── scripts/                       # helper scripts
├── remote-plot/                       # phone/tablet frontend (Vite + Plotly.js)
│   └── src/
│       ├── main.ts                    # WebSocket client + heatmap rendering
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
| `remote-plot/dist` not found | Run `cd remote-plot && pnpm install && pnpm build` |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## License

MIT — see [`LICENSE`](LICENSE) for details.
