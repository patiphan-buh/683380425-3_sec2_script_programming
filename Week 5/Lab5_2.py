# 🔧 เติมโค้ด: Lab 5.2 - Course Enrollment & Collaboration (Set Focus)
# ------------------------------------------------------------
# โจทย์: จำลองการลงทะเบียนเรียนและใช้ Set Operations ในการเปรียบเทียบรายชื่อนักศึกษา

# --- ข้อที่ 1 & 2: กำหนด Set ของนักศึกษาในแต่ละรายวิชา ---
# กำหนดเซตของนักศึกษาวิชา Python และ Java
python_students = {"S001", "S003", "S005", "S007", "S009"}
java_students = {"S002", "S003", "S006", "S007", "S010"}

print(f"Python Students: {python_students}")
print(f"Java Students:   {java_students}\n")


# --- ข้อที่ 3: หานักศึกษาที่เรียนทั้ง 2 วิชา (Intersection) ---
# todo (1): ใช้เมธอด .intersection() หรือเครื่องหมาย & เพื่อหานักศึกษาที่ลงเรียนทั้ง Python และ Java
both_courses = python_students.intersection(java_students)
print(f"Students in Both Courses: {both_courses}")


# --- ข้อที่ 4: หานักศึกษาทั้งหมดแบบไม่ซ้ำกัน (Union) ---
# todo (2): ใช้เมธอด .union() หรือเครื่องหมาย | เพื่อหารายชื่อนักศึกษาทั้งหมดจากทั้งสองวิชา
all_unique_students = python_students.union(java_students)
print(f"All Unique Students: {all_unique_students}")


# --- ข้อที่ 5: หานักศึกษาที่เรียนเฉพาะวิชา Python เท่านั้น (Difference) ---
# todo (3): ใช้เมธอด .difference() หรือเครื่องหมาย - เพื่อหานักศึกษาที่เรียน Python แต่ไม่ได้เรียน Java
only_python = python_students.difference(java_students)
print(f"Students Only in Python: {only_python}")


# --- ข้อที่ 6: หานักศึกษาที่เรียนเพียงวิชาใดวิชาหนึ่งเท่านั้น (Symmetric Difference) ---
# todo (4): ใช้เมธอด .symmetric_difference() หรือเครื่องหมาย ^ เพื่อหานักศึกษาที่ไม่ได้เรียนซ้ำทั้งสองวิชา
exclusive_students = python_students.symmetric_difference(java_students)
print(f"Students in Only One Course: {exclusive_students}\n")


# --- ข้อที่ 7: การลบข้อมูลซ้ำออกจาก List ---
all_students_list = ["S001", "S003", "S005", "S001", "S002"]
print(f"Original List (with duplicates): {all_students_list}")

# todo (5): แปลง all_students_list ให้เป็น set เพื่อลบตัวซ้ำ แล้วแปลงกลับเป็น list
unique_students_list = list(set(all_students_list))
print(f"Unique List (after removing duplicates): {unique_students_list}")