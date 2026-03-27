"""Service layer – provides get_api() to access the active API client."""

import os


def get_api():
    """Return the active API client (real or mock based on USE_MOCK env var)."""
    if os.environ.get("USE_MOCK", "0") == "1":
        from frontend.services.mock_api import mock_api
        return mock_api
    else:
        from frontend.services.api import api
        return api
