# lab4_1.py - Student Management System (List Operations)

print("--- Lab 4.1: Student Management System ---")

# 1) เริ่มต้นด้วย list ว่างสำหรับเก็บชื่อนักศึกษา
student_names = []

# 2) เพิ่มนักศึกษา: รับชื่อจากผู้ใช้ 3 คน แล้ว append() เข้า list
print("\n[1] Add Students")
for i in range(3):
    name = input(f"Enter student name #{i + 1}: ")
    student_names.append(name)

print(f"Current list: {student_names}")

# 3) ค้นหานักศึกษา
print("\n[2] Find a Student")
search_name = input("Enter a name to search for: ")

if search_name in student_names:
    position = student_names.index(search_name)
    print(f"Found '{search_name}' at index {position}")
else:
    print(f"'{search_name}' not found in the list")

# 4) ลบนักศึกษา
print("\n[3] Remove a Student")
remove_name = input("Enter a name to remove: ")

if remove_name in student_names:
    student_names.remove(remove_name)
    print(f"'{remove_name}' has been removed")
else:
    print(f"'{remove_name}' not found, nothing removed")

print(f"Updated list: {student_names}")

# 5) เรียงลำดับรายชื่อตามตัวอักษร
print("\n[4] Sort Students")
student_names.sort()
print(f"Sorted list: {student_names}")

# 6) นับจำนวนนักศึกษาทั้งหมด
print("\n[5] Count Students")
print(f"Total students: {len(student_names)}")


# Challenge
# ระบบจัดการข้อมูลนักเรียนพร้อมเมนู 

student_names = []

while True:
    print("\n===== Student Management System =====")
    print("1. เพิ่มนักเรียน")
    print("2. ลบนักเรียน")
    print("3. ค้นหานักเรียน")
    print("4. เรียงลำดับรายชื่อ")
    print("5. แสดงรายชื่อนักเรียนทั้งหมด")
    print("6. นับจำนวนนักเรียน")
    print("7. ออกจากโปรแกรม")

    choice = input("เลือกเมนู (1-7): ")

    if choice == "1":
        name = input("กรอกชื่อนักเรียน: ")
        student_names.append(name)
        print(f"เพิ่ม '{name}' เรียบร้อยแล้ว")

    elif choice == "2":
        name = input("กรอกชื่อที่ต้องการลบ: ")
        if name in student_names:
            student_names.remove(name)
            print(f"ลบ '{name}' เรียบร้อยแล้ว")
        else:
            print("ไม่พบชื่อนี้ในระบบ")

    elif choice == "3":
        name = input("กรอกชื่อที่ต้องการค้นหา: ")
        if name in student_names:
            position = student_names.index(name)
            print(f"พบ '{name}' ที่ index {position}")
        else:
            print("ไม่พบชื่อนี้ในระบบ")

    elif choice == "4":
        student_names.sort()
        print("เรียงลำดับรายชื่อเรียบร้อยแล้ว")
        print(student_names)

    elif choice == "5":
        print("รายชื่อนักเรียนทั้งหมด:")
        print(student_names)

    elif choice == "6":
        print(f"จำนวนนักเรียนทั้งหมด: {len(student_names)} คน")

    elif choice == "7":
        print("ออกจากโปรแกรม...")
        break

    else:
        print("กรุณาเลือกเมนู 1-7 เท่านั้น")