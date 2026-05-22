"""
SOCKS Proxy Pivot
=================
SOCKS5 proxy server for traffic pivoting and tunneling.

Allows pivoting through compromised hosts or redirecting
traffic through attacker-controlled infrastructure.
"""

import socket
import threading
import time
from typing import Dict, Optional, Tuple


class SOCKSPivot:
    """SOCKS5 proxy server for traffic pivoting."""

    SOCKS5_VERSION = 0x05
    SOCKS5_AUTH_NONE = 0x00
    SOCKS5_CMD_CONNECT = 0x01
    SOCKS5_ATYP_IPV4 = 0x01
    SOCKS5_ATYP_DOMAIN = 0x03
    SOCKS5_ATYP_IPV6 = 0x04

    def __init__(self, listen_addr: str = "0.0.0.0", port: int = 1080):
        self.listen_addr = listen_addr
        self.port = port
        self._running = False
        self._server_sock: Optional[socket.socket] = None
        self._threads: list = []
        self.stats = {
            "connections": 0,
            "bytes_forwarded": 0,
        }

    def start(self) -> bool:
        """Start SOCKS5 proxy server."""
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((self.listen_addr, self.port))
            self._server_sock.listen(10)
            self._running = True

            accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            accept_thread.start()
            self._threads.append(accept_thread)
            return True
        except Exception as e:
            print(f"[SOCKS] Start error: {e}")
            return False

    def _accept_loop(self) -> None:
        """Accept incoming connections."""
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                self.stats["connections"] += 1
                t = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                )
                t.start()
                self._threads.append(t)
            except Exception:
                break

    def _handle_client(self, client_sock: socket.socket, addr: Tuple[str, int]) -> None:
        """Handle SOCKS5 client connection."""
        try:
            client_sock.settimeout(10)

            # SOCKS5 handshake
            version, nmethods = client_sock.recv(2)
            if version != self.SOCKS5_VERSION:
                return

            methods = client_sock.recv(nmethods)
            if self.SOCKS5_AUTH_NONE not in methods:
                client_sock.send(bytes([self.SOCKS5_VERSION, 0xFF]))
                return

            client_sock.send(bytes([self.SOCKS5_VERSION, self.SOCKS5_AUTH_NONE]))

            # SOCKS5 request
            version, cmd, _, atyp = client_sock.recv(4)
            if version != self.SOCKS5_VERSION or cmd != self.SOCKS5_CMD_CONNECT:
                return

            if atyp == self.SOCKS5_ATYP_IPV4:
                dest_addr = socket.inet_ntoa(client_sock.recv(4))
            elif atyp == self.SOCKS5_ATYP_DOMAIN:
                addr_len = ord(client_sock.recv(1))
                dest_addr = client_sock.recv(addr_len).decode()
            else:
                return

            dest_port = int.from_bytes(client_sock.recv(2), "big")

            # Connect to destination
            try:
                dest_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dest_sock.connect((dest_addr, dest_port))

                # Send success response
                client_sock.send(bytes([
                    self.SOCKS5_VERSION, 0x00, 0x00,
                    self.SOCKS5_ATYP_IPV4, 0, 0, 0, 0,
                    0, 0
                ]))

                # Relay data
                self._relay(client_sock, dest_sock)

            except Exception:
                client_sock.send(bytes([self.SOCKS5_VERSION, 0x05, 0x00, 0x01, 0, 0, 0, 0, 0, 0]))

        except Exception:
            pass
        finally:
            client_sock.close()

    def _relay(self, client: socket.socket, dest: socket.socket) -> None:
        """Relay data between client and destination."""
        def forward(src, dst):
            while self._running:
                try:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.send(data)
                    self.stats["bytes_forwarded"] += len(data)
                except Exception:
                    break

        t1 = threading.Thread(target=forward, args=(client, dest), daemon=True)
        t2 = threading.Thread(target=forward, args=(dest, client), daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        dest.close()

    def stop(self) -> None:
        """Stop SOCKS5 proxy server."""
        self._running = False
        if self._server_sock:
            self._server_sock.close()
        for t in self._threads:
            t.join(timeout=1)

    def get_stats(self) -> Dict[str, int]:
        """Return proxy statistics."""
        return {**self.stats, "running": self._running}
