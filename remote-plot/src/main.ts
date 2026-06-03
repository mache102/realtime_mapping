import Plotly from "plotly.js-dist-min";
import "./style.css";
import "./reusable-ui-bundle.css";

/* ─── Types ─── */

interface HeatmapUpdate {
  type: "heatmap_update";
  heatmap_values: number[][];
  heatmap_counts: number[][];
  positions: [number, number][];
  extent: [number, number, number, number];
  sensor_range: { min: number; max: number };
}

/* ─── DOM refs ─── */
const plotDiv = document.getElementById("plot") as HTMLDivElement;
const logArea = document.getElementById("log-area") as HTMLTextAreaElement;
const reconnectBtn = document.getElementById(
  "reconnect-btn",
) as HTMLButtonElement;
const statusIndicator = document.getElementById(
  "status-indicator",
) as HTMLSpanElement;

/* ─── WebSocket ─── */
const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${protocol}//${window.location.host}/ws`;

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectDelay = 1000;
const MAX_RECONNECT_DELAY = 15000;

function log(msg: string): void {
  const time = new Date().toLocaleTimeString();
  logArea.value += `[${time}] ${msg}\n`;
  logArea.scrollTop = logArea.scrollHeight;
}

function setStatus(status: "connecting" | "connected" | "disconnected"): void {
  statusIndicator.className = `status-${status}`;
  if (status === "connecting") {
    statusIndicator.textContent = "Connecting...";
  } else if (status === "connected") {
    statusIndicator.textContent = "Connected";
  } else {
    statusIndicator.textContent = "Disconnected";
  }
}

function scheduleReconnect(): void {
  if (reconnectTimer !== null) return;
  setStatus("connecting");
  log(`Reconnecting in ${(reconnectDelay / 1000).toFixed(1)}s...`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelay);
  reconnectDelay = Math.min(reconnectDelay * 1.5, MAX_RECONNECT_DELAY);
}

function connect(): void {
  if (
    ws &&
    (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)
  ) {
    return;
  }

  log(`Connecting to ${wsUrl}`);
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    log("WebSocket connected");
    setStatus("connected");
    reconnectDelay = 1000;
  };

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: HeatmapUpdate = JSON.parse(event.data);
      if (data.type === "heatmap_update") {
        updatePlot(data);
      }
    } catch (err) {
      log(`Error parsing message: ${err}`);
    }
  };

  ws.onclose = (event: CloseEvent) => {
    log(
      `WebSocket closed (code ${event.code}): ${event.reason || "no reason"}`,
    );
    setStatus("disconnected");
    scheduleReconnect();
  };

  ws.onerror = () => {
    log("WebSocket error");
  };
}

function manualReconnect(): void {
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  if (ws) {
    ws.onclose = null; // prevent auto-reconnect from firing
    ws.close();
    ws = null;
  }

  reconnectDelay = 1000;
  connect();
}

reconnectBtn.addEventListener("click", manualReconnect);

/* ─── Plotly heatmap ─── */
let plotInitialized = false;

const plotLayout = {
  margin: { t: 0, r: 0, b: 36, l: 40 },
  xaxis: {
    title: "X (m)",
    constrain: "domain",
    scaleanchor: "y",
    showgrid: true,
    gridcolor: "var(--black-20)",
    zerolinecolor: "var(--black-50)",
  },
  yaxis: {
    title: "Y (m)",
    showgrid: true,
    gridcolor: "var(--black-20)",
    zerolinecolor: "var(--black-50)",
  },
  paper_bgcolor: "var(--white)",
  plot_bgcolor: "var(--white)",
  font: {
    family: "Roboto, sans-serif",
    color: "var(--black)",
    size: 12,
  },
  dragmode: false as const,
  showlegend: false,
};

const plotConfig = {
  displayModeBar: false,
  responsive: true,
};

function updatePlot(data: HeatmapUpdate): void {
  const { heatmap_values: values, heatmap_counts: counts, positions } = data;
  const [x0, x1, y0, y1] = data.extent;

  // Build a masked z array: where count is 0, set to null
  const z: (number | null)[][] = values.map((row, yi) =>
    row.map((v, xi) => (counts[yi]?.[xi] === 0 ? null : v)),
  );

  const traces: object[] = [
    {
      type: "heatmap",
      z: z,
      x0: x0,
      dx: (x1 - x0) / (values[0]?.length || 1),
      y0: y0,
      dy: (y1 - y0) / values.length,
      colorscale: "Viridis",
      zmin: data.sensor_range.min,
      zmax: data.sensor_range.max,
      hoverinfo: "skip",
      showscale: true,
    },
  ];

  // Add position markers
  if (positions.length > 0) {
    traces.push({
      type: "scatter",
      x: positions.map((p) => p[0]),
      y: positions.map((p) => p[1]),
      mode: "markers",
      marker: {
        color: "var(--red)",
        size: 10,
        symbol: "circle",
      },
      hoverinfo: "skip",
    });
  }

  if (!plotInitialized) {
    Plotly.newPlot(plotDiv, traces, plotLayout, plotConfig);
    plotInitialized = true;
  } else {
    Plotly.react(plotDiv, traces, plotLayout, plotConfig);
  }
}

/* ─── Start ─── */
connect();

// Ping every 15 s to keep the connection alive through proxies / NAT
setInterval(() => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send("ping");
  }
}, 15000);
