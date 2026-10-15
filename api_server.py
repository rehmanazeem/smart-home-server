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
import socket
import time

# --- FastAPI imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# Import utility functions from KeyFunctions
from KeyFunctions.keyFunctions import read_yaml_file, write_yaml_file, update_yaml_file

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
# In-memory Client Socket
# ========================================================================================
client_socket = None

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
    global client_socket
    config = read_yaml_file(CONFIG_PATH)
    if config["esp"]["connect"]:
        return {"message": "Already connected"}
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((config["esp"]["ip"], config["esp"]["port"]))
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
    global client_socket
    config = read_yaml_file(CONFIG_PATH)
    if not config["esp"]["connect"]:
        return {"message": "Already disconnected"}
    try:
        if client_socket:
            client_socket.close()
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
    global client_socket
    config = read_yaml_file(CONFIG_PATH)
    if not config["esp"]["connect"]:
        raise HTTPException(status_code=400, detail="ESP not connected")
    try:
        client_socket.send((str(req.relay_num) + '\n').encode())
        time.sleep(0.1)
        response = client_socket.recv(1024).decode().strip()
        relay_key = f"relay_{req.relay_num}"
        config[relay_key]["state"] = not config[relay_key]["state"]
        update_yaml_file(CONFIG_PATH, relay_key, config[relay_key])
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
    relay_key = f"relay_{relay_num}"
    if relay_key not in config:
        raise HTTPException(status_code=404, detail="Relay not found")
    return {"relay": relay_num, "state": config[relay_key]["state"]}

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
    files = sorted([f for f in os.listdir(log_dir) if f.startswith("log_")])
    if not files:
        return {"logs": []}
    with open(os.path.join(log_dir, files[-1]), "r") as f:
        lines = f.readlines()[-20:]
    return {"logs": lines}

# add function for resetting config file
@app.post("/reset")
def reset_config():
    """
    Reset the configuration file to default values.
    """
    default_config = {
        "esp": {
            "connect": False,
            "ip": "192.168.1.50",
            "port": 8080
        },
        "relay_1": {
            "state": False
        },
        "relay_2": {
            "state": False
        }
    }
    write_yaml_file(CONFIG_PATH, default_config)
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