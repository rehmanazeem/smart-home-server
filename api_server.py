"""
==========================================================================================
FILE        : api_server.py
PROJECT     : Home Automation
DESCRIPTION : REST API server for Home Automation (ESP control).
DATE        : 2025-08-27
==========================================================================================
CODE AUTHOR : Azeem Ur Rehman
==========================================================================================
"""

# ========================================================================================
# Library Imports
# ========================================================================================
import sys
import os
import logging

# --- FastAPI imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# Import utility functions from KeyFunctions
from KeyFunctions.keyFunctions import read_yaml_file, write_yaml_file, update_yaml_file
from espserver.esp_client import EspClient
from espserver.state import default_config, relay_key, tail_latest_log, toggle_state

# ========================================================================================
# Config and Logging Setup
# ========================================================================================
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "Configs", "app_state.yaml"))

# Logging setup (console only for API)
log_formatter = logging.Formatter(
    "{asctime} -> [{levelname:^8}] >>>>> {message} <<<<<",
    datefmt="%Y-%m-%d %H:%M:%S",
    style='{'
)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
logging.basicConfig(level=logging.INFO, handlers=[console_handler])
logger = logging.getLogger("api")

# ========================================================================================
# FastAPI App Initialization
# ========================================================================================

# FastAPI app (API)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================================
# In-memory ESP Client (single TCP connection)
# ========================================================================================
esp = EspClient()

# ========================================================================================
# API Models
# ========================================================================================
class RelayRequest(BaseModel):
    """Request body for relay actions, identifying the target relay number."""
    relay_num: int

# ========================================================================================
# API Endpoints
# ========================================================================================

@app.post("/connect")
def connect():
    """
    Connect to the ESP device using TCP socket.
    """
    config = read_yaml_file(CONFIG_PATH)
    if config["esp"]["connect"]:
        return {"message": "Already connected"}
    try:
        esp.connect(config["esp"]["ip"], config["esp"]["port"])
        config["esp"]["connect"] = True
        write_yaml_file(CONFIG_PATH, config)
        logger.info("✅ Connected to ESP")
        return {"message": "Connected"}
    except Exception as e:
        logger.error(f"❌ Error connecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect")
def disconnect():
    """
    Disconnect from the ESP device.
    """
    config = read_yaml_file(CONFIG_PATH)
    if not config["esp"]["connect"]:
        return {"message": "Already disconnected"}
    try:
        esp.close()
        config["esp"]["connect"] = False
        write_yaml_file(CONFIG_PATH, config)
        logger.info("✅ Disconnected from ESP")
        return {"message": "Disconnected"}
    except Exception as e:
        logger.error(f"❌ Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relay/toggle")
def toggle_relay(req: RelayRequest):
    """
    Toggle the state of a relay on the ESP device.
    """
    config = read_yaml_file(CONFIG_PATH)
    if not config["esp"]["connect"]:
        raise HTTPException(status_code=400, detail="ESP not connected")
    try:
        response = esp.toggle_relay(req.relay_num)
        key = relay_key(req.relay_num)
        update_yaml_file(CONFIG_PATH, key, toggle_state(config, req.relay_num))
        logger.info(f"Toggled relay {req.relay_num}: {response}")
        return {"relay": req.relay_num, "response": response}
    except Exception as e:
        logger.error(f"❌ Error toggling relay: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/relay/{relay_num}/state")
def get_relay_state(relay_num: int):
    """
    Get the current state of a specific relay.
    """
    config = read_yaml_file(CONFIG_PATH)
    key = relay_key(relay_num)
    if key not in config:
        raise HTTPException(status_code=404, detail="Relay not found")
    return {"relay": relay_num, "state": config[key]["state"]}

@app.get("/relays")
def get_all_relays():
    """
    Get the states of all relays.
    """
    config = read_yaml_file(CONFIG_PATH)
    return {
        "relay_1": config["relay_1"]["state"],
        "relay_2": config["relay_2"]["state"]
    }

@app.get("/logs")
def get_logs():
    """
    Fetch the last 20 lines from the latest log file.
    """
    log_dir = os.path.expanduser('~/Library/Logs/LuluApp/Logs')
    return {"logs": tail_latest_log(log_dir)}

# add function for resetting config file
@app.post("/reset")
def reset_config():
    """
    Reset the configuration file to default values.
    """
    write_yaml_file(CONFIG_PATH, default_config())
    logger.info("✅ Config file reset to default values")
    return {"message": "Config file reset to default values"}

@app.get("/esp/connection")
def get_connection_state():
    """
    Get the current connection state of the ESP device.
    """
    config = read_yaml_file(CONFIG_PATH)
    logger.info(f"ESP connection state: {config['esp']['connect']}")
    return {"connected": bool(config["esp"].get("connect", False))}


# ===================================== END OF FILE =====================================