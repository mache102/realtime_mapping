# plotting remote


We run this command from a ubuntu laptop (aka server). 
```bash
ros2 run realtime_mapping realtime_mapper --config genreated_config.yaml
```
The server is connected to ROS, and receives stuff/packets from it.
During experiments, the laptop and an android phone are connected to a LAN that has no outside internet. The laptop cannot be reliably carried around, so a person wants to see the plot in real time from their phone. 

The plot is initialized and updated in `realtime_mapper.py`

```py
def setup_visualization(self):
    """Configure matplotlib visualization."""
    display_config = self.config['mapping'].get('display', {})

    self.fig, self.ax = plt.subplots(figsize=(10, 10))
    self.ax.set_title('Realtime 2D Sensor Mapping')

    # Initial heatmap state
    sensor_range = self.sensor_value_range
    base_cmap = plt.get_cmap(display_config['colormap'])
    if hasattr(base_cmap, 'copy'):
        cmap = base_cmap.copy()
    else:
        cmap = ListedColormap(
            base_cmap(np.linspace(0, 1, base_cmap.N)),
            name=f"{base_cmap.name}_masked"
        )
    cmap.set_bad(color=self.ax.get_facecolor())

    initial_image = np.ma.array(
        self.heatmap_values,
        mask=self.heatmap_counts == 0
    )

    self.im = self.ax.imshow(
        initial_image,
        cmap=cmap,
        vmin=sensor_range['min'],
        vmax=sensor_range['max'],
        origin='lower',
        extent=[
            self.origin_x - self.map_width * self.cell_size / 2,
            self.origin_x + self.map_width * self.cell_size / 2,
            self.origin_y - self.map_height * self.cell_size / 2,
            self.origin_y + self.map_height * self.cell_size / 2
        ]
    )

    show_colorbar = display_config.get('show_colorbar', True)
    if show_colorbar:
        plt.colorbar(self.im, ax=self.ax)

    self.ax.set_xlabel('X (m)')
    self.ax.set_ylabel('Y (m)')

    self.grid_lines = []

    # Marker for current positions
    self.position_marker, = self.ax.plot([], [], 'ro', markersize=8, label='Current Positions')
    self.ax.legend()

    # Animation timing configuration
    self.update_rate = display_config.get('update_rate', 10.0)

    plt.tight_layout()

def setup_data_storage(self):
    """Configure data persistence resources."""
    self.output_config = self.config['output']

    # Ensure the output directory exists
    os.makedirs('output', exist_ok=True)

def update_visualization(self, frame):
    """Refresh the animation frame."""
    with self.lock:
        if self.heatmap_values is not None:
            masked_values = np.ma.array(
                self.heatmap_values,
                mask=self.heatmap_counts == 0
            )
            self.im.set_array(masked_values)

            positions = [pos for pos in self.current_positions.values() if pos is not None]
            if positions:
                xs, ys = zip(*positions)
            else:
                xs, ys = [], []
            self.position_marker.set_data(xs, ys)

    return [self.im, self.position_marker]

```
Requested features:

On laptop, we include a bash script to setup DCHP so that the laptop will have the same local IP address every time the server is started.
After that one time setup, they can run the command above with new flags `--remote-plot` and `--remote-plot-port 8090` (default is 8090 for example) to start the server. this will start a lightweight server module that is also in python.

A line displays the LAN ip addr, for example 10.0.0.221:8090.

On phone, The user opens web browser and enters the local url (optionally bookmarks it).
they can then see the plot in real time.

The webpage uses html, typescript, and css, and plotly js (just use REM units to ensure it scales well). 
On the webpage, the plot is displayed; along with a reconnect button (attempt), and a textarea for all errors/console logs. it can be served via vite or whatever.

the update loop is already infrequent (ie 10hz) and we can just use a websocket connection. 

we just send the relevant data over. 
use fastapi and websockets for backend module.
ensure graceful reconnection (auto) attempts in server, and responsive messages in that textarea in frontend. the usage is portrait mode, so from top to bottom: plot, btn area (small row, only one btn for now), and textarea. no title, desc, navbar, header, footer, etc are needed at all. preferably no page scroll, only the textarea would scroll. 50% area is the plot, since it's a square, and the rest is for the button and textarea.

afte this is done, add a module in the backend, along with a flag for the ros command. if used (it's store_true type), then ros sends random contour-like data for the heatmap. this is used when we can't connect to ROS or simply don't have any hardware to connect to, ensuring we can test with dummy data.


other things to include
the DHCP script: along side the script, include a troubleshotoing markdown file (with bash cmds) so that you can set up the connection stuff without issue.

in readme.md: appedn a section describing how to use all of this new stuff (the remote plot, the dummy data). 


a note for teh websocket: no hardcode, we do something liek this dervied

```js

const protocol =
  window.location.protocol === "https:"
    ? "wss:"
    : "ws:";

const wsUrl =
  `${protocol}//${window.location.host}/ws`;

```

by the time this is all done, the user's experience should be as follows:

laptop. 
0. install python packages etc. 
1. run the DHCP setup script once to ensure the laptop gets the same local IP address every time.
2. run the ros command with the new flags to start the server and the remote plotting module. (if no hardware, include the flag to use dummy data)
3. the server will display the local IP address and port to connect to. 

phone.
1. open web browser.
2. enter the local url. (if bookmarked, just click the bookmark)
3. see the plot in real time, along with any console logs or errors in the textarea. 

and that's it!