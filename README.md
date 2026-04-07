# Doordeer Smart Intercom — Home Assistant Addon

Full Home Assistant integration for **doordeer** doorbell and video intercom devices via the LAN API.

---

## Features

| Feature | Description |
|---|---|
| 🔓 Door unlock | Lock entity + Button entity + Service call |
| 📹 Live camera | RTSP stream (H264) + JPEG snapshot polling |
| 🔑 Credential management | Change device password via UI or HA service |
| 📋 Access log | Timestamped event log with CSV export |
| 📡 RTSP info | HD & SD stream URLs, codec info, VLC command |
| 📊 Sensors | Connection status, log count, stream URL sensor |
| 🖥️ Ingress panel | Built-in dashboard at the Sidebar panel |

---

## Installation

### Step 1 — Add the Addon

1. In HA, go to **Settings → Add-ons → Add-on Store**.
2. Click the menu (⋮) → **Repositories** → paste the URL of this repo.
3. Install **Doordeer Smart Intercom**.

### Step 2 — Configure

Edit the addon configuration:

```yaml
device_ip: "192.168.1.X"      # Your doordeer device's LAN IP
device_port: 3800              # Default port (do not change)
username: "admin"              # Default username
password: "admin"              # Default password (change this!)
rc4_key: "YOUR_KEY_HERE"       # Get this from doordeer vendor (email them)
token_refresh_interval: 540    # Seconds — token refreshed every 9 min (10 min lifetime)
snapshot_interval: 10          # Seconds between background snapshot polls
rtsp_stream: true
log_retention_days: 30
```

> **RC4 Key**: The doordeer API encrypts all login payloads with an RC4 key.  
> Email doordeer smart Inc to obtain your device's key.

### Step 3 — Find Your Device IP

In the **doordeer app**:  
`Devices list → Configurations → Device Status → LAN IP`

### Step 4 — Install the Custom Component

Copy the `custom_components/doordeer/` folder into your HA configuration directory:

```
/config/
  custom_components/
    doordeer/
      __init__.py
      manifest.json
      config_flow.py
      lock.py
      camera.py
      button.py
      sensor.py
      services.yaml
```

Restart Home Assistant, then:  
**Settings → Integrations → + Add Integration → Search "Doordeer"**

---

## Entities Created

| Entity | Type | Description |
|---|---|---|
| `lock.doordeer_door_lock` | Lock | Unlock door; always shows locked (auto-relock) |
| `camera.doordeer_doorbell_camera` | Camera | RTSP HD stream + JPEG snapshot |
| `button.doordeer_unlock_door` | Button | One-tap unlock for dashboards |
| `sensor.doordeer_connection_status` | Sensor | online / offline |
| `sensor.doordeer_access_log_entries` | Sensor | Total log entry count |
| `sensor.doordeer_rtsp_stream_url` | Sensor | Current RTSP main stream URL |

---

## Services

### `doordeer.unlock`
Unlock the door via automation or script. No parameters required.

```yaml
service: doordeer.unlock
```

### `doordeer.change_password`
Update the device login credentials.

```yaml
service: doordeer.change_password
data:
  username: "admin"
  password: "NewSecurePass!"
```

---

## Automation Examples

### Notify on any access event

```yaml
trigger:
  - platform: state
    entity_id: sensor.doordeer_access_log_entries
action:
  - service: notify.mobile_app
    data:
      message: "Doordeer: door activity detected"
```

### Auto-unlock for known person (face/keypad via webhook)

```yaml
trigger:
  - platform: webhook
    webhook_id: doordeer_known_person
action:
  - service: doordeer.unlock
```

### Snapshot on doorbell press

```yaml
trigger:
  - platform: webhook
    webhook_id: doordeer_doorbell_press
action:
  - service: camera.snapshot
    target:
      entity_id: camera.doordeer_doorbell_camera
    data:
      filename: /config/www/doordeer_visitor.jpg
  - service: notify.mobile_app
    data:
      message: "Someone at the door!"
      data:
        image: /local/doordeer_visitor.jpg
```

---

## Lovelace Card Example

```yaml
type: vertical-stack
cards:
  - type: picture-glance
    title: Front Door
    camera_image: camera.doordeer_doorbell_camera
    entities:
      - entity: lock.doordeer_door_lock
      - entity: button.doordeer_unlock_door
      - entity: sensor.doordeer_connection_status
  - type: history-graph
    entities:
      - entity: sensor.doordeer_access_log_entries
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Home Assistant                          │
│  ┌─────────────┐   ┌──────────────────┐ │
│  │ Custom Comp │──▶│  Addon REST API  │ │
│  │ (entities)  │   │  :8099           │ │
│  └─────────────┘   └────────┬─────────┘ │
│                             │           │
│                    ┌────────▼─────────┐ │
│                    │  doordeer client │ │
│                    │  RC4 + token mgr │ │
│                    └────────┬─────────┘ │
└─────────────────────────────┼───────────┘
                              │ LAN HTTP :3800
                    ┌─────────▼─────────┐
                    │  doordeer device  │
                    │  (doorbell/camera)│
                    └───────────────────┘
```

---

## Security Notes

- This API operates **over LAN only** — keep your LAN secure.
- Change the default `admin/admin` credentials immediately after setup.
- The RC4 key and token are stored in memory only — not persisted to disk.
- Tokens expire every 10 minutes and are auto-refreshed.

---

## Support

- Addon issues: open a GitHub issue on this repo
- Device/API issues: contact doordeer smart Inc
- doordeer API version: LAN-2-LAN API V1.0 (2020.12)
