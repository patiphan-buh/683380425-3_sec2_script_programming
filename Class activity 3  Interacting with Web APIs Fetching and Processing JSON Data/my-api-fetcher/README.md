# My API Data Fetcher CLI (Week 10)

**Class Activity 3: Interacting with Web APIs – Fetching and Processing JSON Data**

A command-line app that uses the `requests` library to fetch and process JSON data from the
[JSONPlaceholder](https://jsonplaceholder.typicode.com/) fake REST API.

## Features
| Menu | Function | Endpoint |
|---|---|---|
| 1 | Fetch a Single TODO Item | `GET /todos/{id}` |
| 2 | Fetch All Posts (shows first 5 of 100) | `GET /posts` |
| 3 | Fetch TODOs by User ID (+ completed/pending summary) | `GET /todos?userId={id}` |
| 4 | Exit | – |

- Error handling for `HTTPError`, `ConnectionError`, `Timeout`, `RequestException`, and invalid JSON
- Input validation (non-numbers and numbers ≤ 0 are rejected)

## Project Structure
```
my-api-fetcher/
├── src/
│   ├── __init__.py      # Makes 'src' a Python package
│   └── api_client.py    # APIClient class – all API interaction logic
├── screenshots/         # Run results for menus 1, 2, 3
├── main.py              # CLI menu, calls APIClient and displays results
├── .gitignore
├── README.md
└── requirements.txt
```

## How to Run
```bash
git clone https://github.com/YOUR_USERNAME/my-api-fetcher.git
cd my-api-fetcher
python -m venv venv
# Windows: .\venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Screenshots
### 1. Fetch a Single TODO Item
![Fetch a Single TODO](screenshots/1_fetch_single_todo.png)

### 2. Fetch All Posts
![Fetch All Posts](screenshots/2_fetch_all_posts.png)

### 3. Fetch TODOs by User ID
![Fetch TODOs by User ID](screenshots/3_fetch_user_todos.png)

## Core Concepts
- **API / Endpoint** – structured URLs that return resources
- **HTTP GET** with `requests.get(url, params=..., timeout=10)`
- **Response object** – `status_code`, `ok`, `raise_for_status()`, `json()`
- **JSON → Python** – dicts and lists, iteration, `.get()` access
- **Dependency management** – `pip` and `requirements.txt`
