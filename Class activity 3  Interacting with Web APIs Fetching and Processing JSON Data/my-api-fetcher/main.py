# my-api-fetcher/main.py
"""CLI entry point: Simple API Data Fetcher (Week 10)."""
import os
import sys

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from api_client import APIClient  # noqa: E402

LINE = "=" * 45


def display_menu():
    """Show the main menu."""
    print(f"\n{LINE}")
    print("   API Data Fetcher Menu (JSONPlaceholder)")
    print(LINE)
    print("1. ดึงข้อมูล TODO รายการเดียว (Fetch a Single TODO Item)")
    print("2. ดึงโพสต์ทั้งหมด (Fetch All Posts)")
    print("3. ดึงรายการ TODO ตามรหัสผู้ใช้ (Fetch TODOs by User ID)")
    print("4. ออกจากโปรแกรม (Exit)")
    print(LINE)


def read_positive_int(prompt):
    """Read a positive integer from the user; return None if input is invalid."""
    try:
        value = int(input(prompt).strip())
    except ValueError:
        print("[WARN] กรุณากรอกตัวเลขเท่านั้น")
        return None
    if value <= 0:
        print("[WARN] ตัวเลขต้องมากกว่า 0")
        return None
    return value


def handle_fetch_single_todo(client):
    todo_id = read_positive_int("กรอกรหัส TODO (เช่น 1, 5, 10): ")
    if todo_id is None:
        return
    todo = client.fetch_single_todo(todo_id)
    if not todo:
        print(f"ไม่สามารถดึงข้อมูล TODO ID {todo_id} ได้")
        return
    status = "✅ เสร็จแล้ว (Completed)" if todo.get("completed") else "⏳ ยังไม่เสร็จ (Pending)"
    print("\n--- รายละเอียด TODO (TODO Item Details) ---")
    print(f"ID      : {todo.get('id')}")
    print(f"User ID : {todo.get('userId')}")
    print(f"Title   : {todo.get('title')}")
    print(f"Status  : {status}")
    print("-" * 45)


def handle_fetch_all_posts(client, show=5):
    posts = client.fetch_all_posts()
    if not posts:
        print("ไม่สามารถดึงข้อมูลโพสต์ได้")
        return
    print(f"\n--- แสดง {min(show, len(posts))} รายการแรก (จากทั้งหมด {len(posts)} รายการ) ---")
    for post in posts[:show]:
        print(f"\n[{post.get('id')}] Post ID: {post.get('id')} | User ID: {post.get('userId')}")
        print(f"    หัวข้อ (Title): {post.get('title')}")
        print(f"    เนื้อหา (Body) : {post.get('body', '').replace(chr(10), ' ')[:60]}...")
    if len(posts) > show:
        print(f"\n... และยังมีอีก {len(posts) - show} โพสต์ที่ไม่ได้แสดงบนหน้าจอ")
    print("-" * 45)


def handle_fetch_user_todos(client):
    user_id = read_positive_int("กรอกรหัสผู้ใช้ User ID (เช่น 1, 2, 3): ")
    if user_id is None:
        return
    todos = client.fetch_user_todos(user_id)
    if todos is None:
        print(f"ไม่สามารถดึงข้อมูล TODO ของ User ID {user_id} ได้")
        return
    if not todos:
        print(f"ไม่พบ TODO ของ User ID {user_id}")
        return
    done = sum(1 for t in todos if t.get("completed"))
    print(f"\n--- TODO ของ User ID {user_id} ({len(todos)} รายการ) ---")
    for todo in todos:
        status = "Completed" if todo.get("completed") else "Pending"
        print(f"ID: {todo.get('id'):>3} | {status:<9} | {todo.get('title')}")
    print(f"\nสรุป: เสร็จแล้ว {done} / ยังไม่เสร็จ {len(todos) - done} (ทั้งหมด {len(todos)})")
    print("-" * 45)


def main():
    client = APIClient()
    actions = {
        "1": handle_fetch_single_todo,
        "2": handle_fetch_all_posts,
        "3": handle_fetch_user_todos,
    }
    while True:
        display_menu()
        choice = input("กรุณาเลือกเมนู (1-4): ").strip()
        if choice == "4":
            print("ออกจากโปรแกรม API Data Fetcher แล้ว ขอบคุณครับ/ค่ะ 👋")
            break
        action = actions.get(choice)
        if action:
            action(client)
        else:
            print("[WARN] เมนูไม่ถูกต้อง กรุณาเลือก 1-4")


if __name__ == "__main__":
    main()
