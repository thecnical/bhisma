"""
Network Topology Mapper
=========================
WiFi network topology discovery and mapping.

Discovers APs, clients, and their relationships to build
a comprehensive network graph for attack planning.
"""

import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class NetworkNode:
    """Network node (AP or client)."""
    mac: str
    node_type: str  # 'ap' | 'client'
    ssid: Optional[str]
    ip: Optional[str]
    signal: int
    channel: int
    manufacturer: Optional[str]
    timestamp: float


@dataclass
class NetworkEdge:
    """Connection between nodes."""
    source_mac: str
    target_mac: str
    connection_type: str  # 'associated' | 'adhoc' | 'wds'
    signal_strength: int
    timestamp: float


class TopologyMapper:
    """WiFi network topology mapping engine."""

    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: List[NetworkEdge] = []
        self.aps: Set[str] = set()
        self.clients: Set[str] = set()
        self.stats = {
            "nodes_discovered": 0,
            "edges_discovered": 0,
        }

    def add_ap(self, bssid: str, ssid: str, channel: int,
               signal: int, manufacturer: Optional[str] = None) -> None:
        """Add access point to topology."""
        node = NetworkNode(
            mac=bssid,
            node_type="ap",
            ssid=ssid,
            ip=None,
            signal=signal,
            channel=channel,
            manufacturer=manufacturer,
            timestamp=time.time(),
        )
        self.nodes[bssid] = node
        self.aps.add(bssid)
        self.stats["nodes_discovered"] += 1

    def add_client(self, mac: str, bssid: str, signal: int,
                   ip: Optional[str] = None) -> None:
        """Add client to topology and create edge to AP."""
        node = NetworkNode(
            mac=mac,
            node_type="client",
            ssid=None,
            ip=ip,
            signal=signal,
            channel=0,
            manufacturer=None,
            timestamp=time.time(),
        )
        self.nodes[mac] = node
        self.clients.add(mac)
        self.stats["nodes_discovered"] += 1

        # Create edge to AP
        edge = NetworkEdge(
            source_mac=mac,
            target_mac=bssid,
            connection_type="associated",
            signal_strength=signal,
            timestamp=time.time(),
        )
        self.edges.append(edge)
        self.stats["edges_discovered"] += 1

    def get_topology(self) -> Dict[str, Any]:
        """Get complete topology as JSON-serializable dict."""
        return {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "edges": [asdict(e) for e in self.edges],
            "aps": list(self.aps),
            "clients": list(self.clients),
            "timestamp": time.time(),
        }

    def get_ap_clients(self, bssid: str) -> List[str]:
        """Get all clients connected to a specific AP."""
        return [e.source_mac for e in self.edges if e.target_mac == bssid]

    def get_client_ap(self, mac: str) -> Optional[str]:
        """Get the AP a client is connected to."""
        for edge in self.edges:
            if edge.source_mac == mac:
                return edge.target_mac
        return None

    def find_isolated_aps(self) -> List[str]:
        """Find APs with no connected clients."""
        ap_with_clients = {e.target_mac for e in self.edges}
        return list(self.aps - ap_with_clients)

    def find_multi_ap_clients(self) -> List[str]:
        """Find clients seen on multiple APs (roaming)."""
        client_ap_count: Dict[str, Set[str]] = {}
        for edge in self.edges:
            if edge.source_mac not in client_ap_count:
                client_ap_count[edge.source_mac] = set()
            client_ap_count[edge.source_mac].add(edge.target_mac)
        return [mac for mac, aps in client_ap_count.items() if len(aps) > 1]

    def clear(self) -> None:
        """Clear all topology data."""
        self.nodes.clear()
        self.edges.clear()
        self.aps.clear()
        self.clients.clear()
        self.stats = {"nodes_discovered": 0, "edges_discovered": 0}

    def get_stats(self) -> Dict[str, int]:
        """Return topology statistics."""
        return {
            **self.stats,
            "total_aps": len(self.aps),
            "total_clients": len(self.clients),
            "total_edges": len(self.edges),
        }
