# spreadsheet-automator/main.py
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from excel_processor import ExcelProcessor

def main():
    """
    Main entry point for the spreadsheet automation application.
    """
    input_file = os.path.join('data', 'input_sales.xlsx')
    output_file = os.path.join('data', 'output_sales_report.xlsx')

    # Ensure the 'data' directory exists
    os.makedirs('data', exist_ok=True)

    # Check if the input file exists as it's required for the prototype
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        print("Please create 'input_sales.xlsx' in the 'data' folder with sample sales data (Product Name, Quantity, Unit Price).")
        print("Refer to the README.md for example content.")
        return

    processor = ExcelProcessor()
    print(f"Starting sales data processing from '{input_file}'...")
    success = processor.process_sales_data(input_file, output_file)

    if success:
        print(f"Sales report successfully generated and saved to '{output_file}'.")
    else:
        print("Failed to generate sales report.")

if __name__ == "__main__":
    main()
