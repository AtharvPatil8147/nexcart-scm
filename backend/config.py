"""Compatibility import path for application settings.

Use ``backend.core.settings`` in new code.
"""

from backend.core.settings import Settings, settings, startup_health_check

__all__ = ["Settings", "settings", "startup_health_check"]
