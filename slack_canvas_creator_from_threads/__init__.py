"""Slack Canvas Creator from Threads - A Slack app for creating Canvas from thread discussions."""

__version__ = "0.1.0"

from .app import CanvasCreatorApp
from .main import app

__all__ = ["CanvasCreatorApp", "app"]
