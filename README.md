# Doordeer Smart Intercom — HA Custom Integration

Local LAN integration for doordeer doorbell and video intercom devices.
Works with **all** Home Assistant install types including HA Core.

## What it creates

| Entity | Description |
|---|---|
| `lock.doordeer_door_lock` | Unlock the door |
| `camera.doordeer_doorbell_camera` | Live RTSP stream + JPEG snapshots |
| `button.doordeer_unlock_door` | Dashboard tap-to-unlock |
| `sensor.doordeer_connection_status` | connected / disconnected |
| `sensor.doordeer_rtsp_stream` | RTSP URL + codec info |
| `sensor.doordeer_access_log_entries` | Event count |

## Installation

### Option A — HACS (recommended)
1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/Beef-well/doordeer` → Category: Integration
3. Install **Doordeer Smart Intercom**
4. Restart HA

### Option B — Manual
1. Copy `custom_components/doordeer/` into your `/config/custom_components/` folder
2. Restart HA

### Setup
Settings → Integrations → Add Integration → Search **Doordeer**

You will need:
- Device LAN IP (doordeer app → Devices → Configurations → Device Status)
- Username / Password (default: `admin` / `admin`)
- RC4 key (email doordeer smart Inc to obtain this)

## Services

```yaml
# Unlock door
service: doordeer.unlock

# Change password
service: doordeer.change_password
data:
  password: "NewPassword123"
```

## Lovelace example

```yaml
type: picture-glance
title: Front Door
camera_image: camera.doordeer_doorbell_camera
entities:
  - entity: lock.doordeer_door_lock
  - entity: button.doordeer_unlock_door
  - entity: sensor.doordeer_connection_status
```
