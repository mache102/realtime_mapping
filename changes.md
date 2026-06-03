# v1.0.0

## 2026-06-03

### 4. Added rclpy stubs so --dummy-data runs without ROS installed

**Commit hash:** `f97d152`

#### User-facing summary
The mapper no longer requires `rclpy` to be installed when using `--dummy-data`. If ROS is missing the script falls back to **minimal stubs** covering the Node, Logger, and Clock APIs.

#### Technical changes
- Created `ros_stubs.py` with `Node`, `_LoggerStub`, `_ClockStub`, and `_RclpyStub` covering the exact surface area used by `realtime_mapper.py`
- Made `rclpy` import conditional via `try/except ImportError` with fallback to stubs
- Fixed `update_rate` ordering: extracted from config in `__init__` before `_setup_dummy_data()` is called
- Added `_HAS_ROS` guard in `main()` that prints a clear error and exits when ROS mode is attempted without `rclpy`
- Added `__init__.py` to outer package directory to support direct script execution

### 3. Rewrote root README with uv-based setup and merged package docs

**Commit hash:** `0698669`

#### User-facing summary
The root `README.md` now provides a **linear, copy-pasteable setup flow** from scratch: Python environment (`uv venv`), local verification with matplotlib, remote plot extension, and optional ROS integration. All relevant content from `realtime_mapping/README.md` has been merged in.

#### Technical changes
- Merged key features, configuration reference, and usage instructions from `realtime_mapping/README.md` into root `README.md`
- Restructured flow: Setup → Local Verify → Remote Plot → ROS Hardware
- Added full config YAML reference with section table
- Added Controlling the Visualiser and expanded Troubleshooting sections

### 2. Added dummy data generator for offline testing

**Commit hash:** `2b95fc7`

#### User-facing summary
The mapper can now run **without ROS hardware** by generating synthetic contour-like heatmap data using the new `--dummy-data` flag.

#### Technical changes
- Added `DummyDataGenerator` module (`realtime_mapping/realtime_mapping/dummy_data_generator.py`) with Lissajous-trajectory Gaussian blobs
- Added `--dummy-data` CLI flag to `realtime_mapper.py` that bypasses ROS subscriptions
- Enables end-to-end testing of remote plot with no hardware required

### 1. Added remote plot server with browser-based viewer

**Commit hash:** `9668fe0`

#### User-facing summary
Users can now view the live heatmap on a **phone or tablet browser** while the mapper runs on the laptop. The laptop displays a LAN URL after startup.

#### Technical changes
- Added `RemotePlotServer` module (`realtime_mapping/realtime_mapping/remote_plot_server.py`) with FastAPI + WebSocket streaming
- Added Plotly.js frontend (`remote-plot/`) with TypeScript, Vite, and Griz Style CSS
- Added `--remote-plot` and `--remote-plot-port` CLI flags to `realtime_mapper.py`
- Added DHCP setup script (`scripts/setup_dhcp.sh`) and troubleshooting guide
- Updated `.gitignore` for remote-plot build artifacts
- Updated `README.md` with remote plot usage instructions
