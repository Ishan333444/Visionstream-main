"""Manual database smoke check; kept import-safe for pytest collection."""
from backend.services.analytics_repository import get_latest


if __name__ == "__main__":
    print(get_latest())
