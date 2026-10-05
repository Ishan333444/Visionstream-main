import requests

from config import API_URL


def get_health():
    response = requests.get(
        f"{API_URL}/health",
        timeout=2,
    )
    response.raise_for_status()
    return response.json()


def get_stats():
    response = requests.get(
        f"{API_URL}/stats",
        timeout=2,
    )
    response.raise_for_status()
    return response.json()


def get_events(limit=None):
    params = {}

    if limit is not None:
        params["limit"] = limit

    response = requests.get(
        f"{API_URL}/events",
        params=params,
        timeout=2,
    )

    response.raise_for_status()

    return response.json()


def get_analytics():
    response = requests.get(
        f"{API_URL}/analytics",
        timeout=2,
    )
    response.raise_for_status()
    return response.json()