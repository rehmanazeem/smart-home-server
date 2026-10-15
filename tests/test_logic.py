"""Tests for pure logic and the REST layer, using a fake socket (no hardware)."""
import pytest
from fastapi.testclient import TestClient

import api_server
from espserver.esp_client import EspClient, format_relay_command
from espserver.state import default_config, relay_key, tail_latest_log, toggle_state
from KeyFunctions.keyFunctions import read_yaml_file, write_yaml_file


class FakeSocket:
    def __init__(self):
        self.sent, self.closed, self.addr = [], False, None

    def settimeout(self, t): pass
    def connect(self, addr): self.addr = addr
    def send(self, data): self.sent.append(data)
    def recv(self, n): return b"OK relay\r\n"
    def close(self): self.closed = True


def test_command_format():
    assert format_relay_command(2) == b"2\n"


def test_toggle_state_and_key():
    cfg = default_config()
    assert relay_key(1) == "relay_1"
    assert toggle_state(cfg, 1) == {"state": True}
    assert toggle_state(cfg, 1) == {"state": False}
    with pytest.raises(KeyError):
        toggle_state(cfg, 9)


def test_tail_latest_log(tmp_path):
    assert tail_latest_log(str(tmp_path)) == []
    (tmp_path / "log_2025-01-01").write_text("old\n")
    (tmp_path / "log_2025-01-02").write_text("".join(f"l{i}\n" for i in range(30)))
    out = tail_latest_log(str(tmp_path))
    assert len(out) == 20 and out[-1] == "l29\n"


def test_client_roundtrip():
    sock = FakeSocket()
    c = EspClient(lambda: sock, settle_s=0)
    c.connect("192.168.1.50", 8080)
    assert sock.addr == ("192.168.1.50", 8080)
    assert c.toggle_relay(1) == "OK relay"
    assert sock.sent == [b"1\n"]
    c.close()
    assert sock.closed


@pytest.fixture
def client(tmp_path, monkeypatch):
    cfg = tmp_path / "state.yaml"
    write_yaml_file(str(cfg), default_config())
    monkeypatch.setattr(api_server, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(api_server, "esp", EspClient(FakeSocket, settle_s=0))
    return TestClient(api_server.app), cfg


def test_api_flow(client):
    http, cfg = client
    assert http.post("/relay/toggle", json={"relay_num": 1}).status_code == 400
    assert http.post("/connect").json() == {"message": "Connected"}
    assert http.post("/connect").json() == {"message": "Already connected"}
    assert http.post("/relay/toggle", json={"relay_num": 1}).json() == {"relay": 1, "response": "OK relay"}
    assert http.get("/relay/1/state").json() == {"relay": 1, "state": True}
    assert http.get("/relays").json() == {"relay_1": True, "relay_2": False}
    assert http.get("/relay/7/state").status_code == 404
    assert http.get("/esp/connection").json() == {"connected": True}
    assert http.post("/disconnect").json() == {"message": "Disconnected"}
    http.post("/reset")
    assert read_yaml_file(str(cfg)) == default_config()
