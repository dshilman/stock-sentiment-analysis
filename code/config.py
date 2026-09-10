"""Application configuration for the Mboum Finance API.

Reads the RapidAPI key from the ``RAPIDAPI_KEY`` environment variable at
request time (via :meth:`Config.get_headers`) rather than at import time, so
the module can be imported even when the key is not yet set (e.g. before a
``.env`` file is loaded).
"""

import os


class Config:
    """Static configuration and header builder for the finance API."""

    NEWS_API_URL = "https://mboum-finance.p.rapidapi.com/v1/markets/news"
    HISTORY_API_URL = "https://mboum-finance.p.rapidapi.com/v1/markets/stock/history"
    RAPIDAPI_HOST = "mboum-finance.p.rapidapi.com"
    RAPIDAPI_KEY_ENV = "RAPIDAPI_KEY"

    @classmethod
    def get_api_key(cls) -> str:
        """Return the RapidAPI key from the environment.

        Raises:
            RuntimeError: if the key environment variable is not set.
        """
        api_key = os.environ.get(cls.RAPIDAPI_KEY_ENV)
        if not api_key:
            raise RuntimeError(
                f"Environment variable '{cls.RAPIDAPI_KEY_ENV}' is not set."
            )
        return api_key

    @classmethod
    def get_headers(cls) -> dict:
        """Build the request headers required by the RapidAPI endpoint."""
        return {
            "X-RapidAPI-Key": cls.get_api_key(),
            "X-RapidAPI-Host": cls.RAPIDAPI_HOST,
        }


# Backwards-compatible alias for existing imports (`from config import config`).
config = Config
