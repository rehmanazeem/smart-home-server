"""TCP client for the ESP8266 relay board (the only place that touches sockets)."""
import socket
import time
from typing import Callable

SocketFactory = Callable[[], socket.socket]


def format_relay_command(relay_num: int) -> bytes:
    """Wire format understood by btnRebounceTCP.ino: the relay number plus a newline."""
    return (str(relay_num) + "\n").encode()


class EspClient:
    """Holds the single TCP connection to the ESP. Inject `socket_factory` to fake it in tests."""

    def __init__(
        self,
        socket_factory: SocketFactory = lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        settle_s: float = 0.1,
    ) -> None:
        self._factory = socket_factory
        self._settle_s = settle_s
        self._sock: socket.socket | None = None

    def connect(self, ip: str, port: int, timeout_s: float = 5) -> None:
        """Open the connection (replaces any previous socket reference)."""
        self._sock = self._factory()
        self._sock.settimeout(timeout_s)
        self._sock.connect((ip, port))

    def close(self) -> None:
        """Close the socket if one is open."""
        if self._sock:
            self._sock.close()

    def toggle_relay(self, relay_num: int) -> str:
        """Send a toggle command and return the ESP's stripped reply."""
        self._sock.send(format_relay_command(relay_num))
        time.sleep(self._settle_s)
        return self._sock.recv(1024).decode().strip()
