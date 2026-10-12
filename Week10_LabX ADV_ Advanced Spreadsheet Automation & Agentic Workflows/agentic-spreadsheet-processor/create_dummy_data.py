# agentic-spreadsheet-processor/create_dummy_data.py
# Creates data/input_data.xlsx (sheet "SalesData") used by the agent.
import os
import openpyxl

def create_dummy_data(path=os.path.join("data", "input_data.xlsx")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SalesData"  # must match source_sheet in the config

    rows = [
        ("Product Name", "Quantity", "Unit Price"),
        ("Laptop", 2, 1200.50),
        ("Mouse", 5, 25.00),
        ("Keyboard", 3, 75.99),
        ("Monitor", 1, 300.00),
        ("Projector", 1, 850.00),
        ("Webcam", 10, 45.00),
        ("Headset", 4, 99.99),
        ("SSD", 2, 180.00),
        ("Router", 1, 70.00),
    ]
    for row in rows:
        ws.append(row)

    wb.save(path)
    print(f"Dummy input data created at '{path}'.")

if __name__ == "__main__":
    create_dummy_data()
