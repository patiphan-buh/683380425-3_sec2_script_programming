# lab4_2.py - Geometric Calculations (Tuples & Immutability)

import math

print("--- Lab 4.2: Geometric Calculations ---")

# 1) กำหนดจุดสองจุดด้วย tuple: point1 และ point2
point1 = (3, 4)
point2 = (6, 8)

# 2) เข้าถึงค่าพิกัด x, y ของแต่ละจุด
print("\n[1] Access Coordinates")
print(f"Point 1: x = {point1[0]}, y = {point1[1]}")
print(f"Point 2: x = {point2[0]}, y = {point2[1]}")

# 3) ทดลองแก้ไขค่าใน tuple เพื่อแสดงให้เห็นว่า tuple เปลี่ยนแปลงไม่ได้ (immutable)
print("\n[2] Attempt Modification (Immutability Demonstration)")
try:
    point1[0] = 5  # บรรทัดนี้จะทำให้เกิด TypeError เพราะ tuple แก้ไขไม่ได้
except TypeError as e:
    print(f"Error trying to modify tuple: {e}")

# 4) คำนวณระยะห่างระหว่างจุดสองจุดด้วยสูตรระยะทาง
# distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
print("\n[3] Calculate Distance")
distance = math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
print(f"Distance between point1 {point1} and point2 {point2}: {distance}")

#Challenge

print("\n\n--- Challenge: Calculate Distance from User Input ---")

print("Enter Point 1")
x1 = float(input("x1: "))
y1 = float(input("y1: "))
point1 = (x1, y1)

print("\nEnter Point 2")
x2 = float(input("x2: "))
y2 = float(input("y2: "))
point2 = (x2, y2)

distance = math.sqrt((point2[0] - point1[0]) ** 2 +
                     (point2[1] - point1[1]) ** 2)

print(f"\nPoint 1: {point1}")
print(f"Point 2: {point2}")
print(f"Distance = {distance}")