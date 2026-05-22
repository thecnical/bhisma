"""FastAPI web dashboard with real-time WebSocket updates."""
from bhisma.dashboard.server import start_dashboard
from bhisma.dashboard.websocket import DashboardWebsocket

__all__ = ['start_dashboard', 'DashboardWebsocket']
