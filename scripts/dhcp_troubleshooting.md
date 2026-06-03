# DHCP / Static IP Troubleshooting

This guide helps you debug network issues when setting up the laptop
for the remote plot server. Run commands on the **laptop** (the ROS
machine).

---

## Quick checks

```bash
# 1. Is the interface up?
ip link show

# 2. Does it have an IP?
ip -4 addr show

# 3. Can you reach the gateway?
ip route | grep default
ping -c 3 $(ip route | awk '/^default/ {print $3}')

# 4. Is DNS working?
ping -c 3 8.8.8.8
ping -c 3 google.com
```

---

## Scenario: "Phone cannot reach the laptop"

Make sure both devices are on the **same LAN subnet**.

On the laptop:
```bash
ip -4 addr show | grep inet
```

On the phone, open the browser and try:
- `http://<LAPTOP_IP>:8090`

If the page doesn't load:

1. **Check the laptop firewall:**
   ```bash
   sudo ufw status
   # If ufw is active, allow the port:
   sudo ufw allow 8090/tcp
   ```

2. **Check if the server is listening:**
   ```bash
   ss -tlnp | grep 8090
   ```
   You should see `0.0.0.0:8090` in the output.

3. **Test from laptop itself:**
   ```bash
   curl -I http://localhost:8090
   ```
   Should return `HTTP/1.1 200 OK`.

---

## Scenario: "netplan apply fails"

```bash
# Check config syntax
sudo netplan try

# View detailed error
sudo netplan --debug apply

# Restore previous config
sudo cp /etc/netplan/backup/<original>.yaml.bak.* /etc/netplan/<original>.yaml
sudo rm /etc/netplan/99-realtime-mapping-static.yaml
sudo netplan apply
```

## Scenario: "Wi-Fi keeps dropping / IP changes"

This can happen if NetworkManager is also managing the interface.
Disable NetworkManager for this interface:

```bash
# Check if NetworkManager manages it
nmcli device status

# Option A: Let netplan handle it
# Edit /etc/netplan/99-realtime-mapping-static.yaml and add:
#   renderer: networkd
# (this is already the default in setup_dhcp.sh)

# Option B: Configure static IP via NetworkManager instead
nmcli con show
# Find your connection name, then:
sudo nmcli con mod "<connection-name>" ipv4.addresses 10.0.0.221/24
sudo nmcli con mod "<connection-name>" ipv4.gateway 10.0.0.1
sudo nmcli con mod "<connection-name>" ipv4.dns "8.8.8.8,8.8.4.4"
sudo nmcli con mod "<connection-name>" ipv4.method manual
sudo nmcli con down "<connection-name>" && sudo nmcli con up "<connection-name>"
```

---

## Scenario: "No internet after applying static IP"

The static IP config uses the detected gateway and DNS. If the
gateway address is wrong, internet won't work.

```bash
# Find the correct gateway (look at your router's admin page, or):
# Temporarily revert to DHCP to discover gateway:
sudo rm /etc/netplan/99-realtime-mapping-static.yaml
sudo netplan apply
ip route | grep default   # note the gateway IP
```

Then re-run `setup_dhcp.sh` and verify the gateway.

---

## Scenario: "Android phone on the same Wi-Fi but can't connect"

Some Android devices block local network access on mobile data / Wi-Fi
assist. Disable **"Mobile data always active"** in Developer Options,
and ensure **Wi-Fi** is the primary connection.

Also try:
- Use Chrome (some WebSocket implementations don't work in older
  Android WebViews).
- Disable any VPN on the phone.

---

## Scenario: "I don't want a static IP, just want to know the IP each time"

Skip `setup_dhcp.sh` entirely. Instead, check your IP before running
the mapper:

```bash
hostname -I | awk '{print $1}'
```

Or add this to your `.bashrc`:
```bash
alias myip="hostname -I | awk '{print \$1}'"
```

The remote plot server prints the LAN URL on startup regardless of
whether you ran `setup_dhcp.sh`.

---

## Useful commands reference

| Command | What it does |
|---------|-------------|
| `ip -br addr` | List interfaces and IPs (compact) |
| `ip route \| grep default` | Show default gateway |
| `ss -tlnp \| grep 8090` | Check if server is listening |
| `sudo ufw status` | Firewall status |
| `sudo ufw allow 8090/tcp` | Open port in firewall |
| `sudo netplan try` | Test netplan config with rollback |
| `nmcli device status` | NetworkManager device list |
| `ping 10.0.0.221` | Test connectivity to a host |
