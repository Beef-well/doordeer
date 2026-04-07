"""Constants for the Doordeer integration."""

DOMAIN = "doordeer"

DEFAULT_PORT = 3800
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

TOKEN_LIFETIME = 600       # 10 minutes per API spec
TOKEN_REFRESH_BEFORE = 60  # refresh 60s before expiry

CONF_DEVICE_IP = "device_ip"
CONF_DEVICE_PORT = "device_port"
CONF_RC4_KEY = "rc4_key"

PLATFORMS = ["lock", "camera", "button", "sensor"]
