# my-api-fetcher/src/api_client.py
"""API client for JSONPlaceholder (https://jsonplaceholder.typicode.com)."""
import json

import requests


class APIClient:
    """A client to interact with the JSONPlaceholder API."""

    BASE_URL = "https://jsonplaceholder.typicode.com"

    def _make_request(self, endpoint, params=None):
        """Send a GET request to an endpoint and return the parsed JSON (or None on failure)."""
        url = f"{self.BASE_URL}{endpoint}"
        print(f"[INFO] กำลังส่งคำขอ (GET) ไปที่: {url}" + (f" params={params}" if params else ""))
        response = None
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # 4xx / 5xx -> HTTPError
            print(f"[INFO] สถานะ: {response.status_code} (ok={response.ok})")
            return response.json()
        except requests.exceptions.HTTPError as errh:
            print(f"[ERROR] HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(f"[ERROR] เชื่อมต่อไม่ได้: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"[ERROR] หมดเวลา (Timeout): {errt}")
        except requests.exceptions.RequestException as err:
            print(f"[ERROR] เกิดข้อผิดพลาดที่ไม่คาดคิด: {err}")
        except (json.JSONDecodeError, ValueError):
            text = response.text[:100] if response is not None else ""
            print(f"[ERROR] แปลง JSON ไม่ได้: {text}...")
        return None

    def fetch_single_todo(self, todo_id):
        """Fetch a single TODO item by its ID."""
        return self._make_request(f"/todos/{todo_id}")

    def fetch_all_posts(self):
        """Fetch the list of all posts."""
        return self._make_request("/posts")

    def fetch_user_todos(self, user_id):
        """Fetch all TODOs belonging to a user ID."""
        return self._make_request("/todos", params={"userId": user_id})
