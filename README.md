# Realtime Mapping Workspace

This repository hosts the ROS 2 *realtime_mapping* package along with helper scripts, configuration files, and documentation. Use it as a workspace root when cloning or developing the system outside an existing ROS 2 workspace.

## Contents

- `realtime_mapping/` – ROS 2 package containing the mapper node, synthetic publisher, topic inspector, configs, and launch files.
- `README.md` – this workspace overview.
- `install/`, `log/`, `output/` – directories generated during builds or runtime (ignored by git).

For detailed usage, build steps, and troubleshooting tips, refer to `realtime_mapping/README.md` and `realtime_mapping/BUILD_INSTRUCTIONS.md`.

---

## Remote Plot (Phone / Tablet Viewer)

The remote plot feature lets you view the live heatmap on a phone or tablet
browser while the mapper runs on the laptop. It uses **FastAPI + WebSockets**
on the backend and a **Plotly.js** frontend styled with the Griz design
system.

### Laptop Setup

1. **Install Python dependencies:**
   ```bash
   pip3 install fastapi uvicorn websockets
   ```

2. **Build the frontend (one time):**
   ```bash
   cd remote-plot
   pnpm install
   pnpm build
   cd ..
   ```

3. **(Optional) Reserve a static LAN IP** so the phone always reaches the
   same URL:
   ```bash
   sudo ./scripts/setup_dhcp.sh
   ```
   See `scripts/dhcp_troubleshooting.md` if you encounter issues.

4. **Run the mapper with remote plotting:**
   ```bash
   python3 src/realtime_mapping/realtime_mapping/realtime_mapper.py \
     --config config/generated_config.yaml \
     --remote-plot \
     --remote-plot-port 8090
   ```

   The terminal prints the LAN URL (e.g. `http://10.0.0.221:8090`).

### Phone / Tablet

1. Connect to the **same LAN** as the laptop.
2. Open a web browser (Chrome recommended).
3. Enter the URL shown in the laptop terminal.
4. The page loads with:
   - **Plot** (top 50 %) — live-updating heatmap.
   - **Reconnect button** — tap to manually restart the WebSocket.
   - **Log area** (bottom) — connection status and error messages.

### Firewall

If the phone cannot reach the laptop, allow the port:
```bash
sudo ufw allow 8090/tcp
```

---

## Dummy Data Mode

When you don't have ROS hardware available, use the `--dummy-data` flag
to generate synthetic contour-like heatmap patterns. No ROS topics are
subscribed to in this mode.

```bash
python3 src/realtime_mapping/realtime_mapping/realtime_mapper.py \
  --dummy-data \
  --remote-plot \
  --remote-plot-port 8090
```

The dummy generator simulates an agent moving in a Lissajous pattern while
depositing Gaussian-shaped sensor values, producing visually interesting
heatmap data.

Combine `--dummy-data` with `--remote-plot` to test the full pipeline
end-to-end without any hardware.
