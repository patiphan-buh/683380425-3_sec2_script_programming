def add(a, b):
    """Returns the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Returns the difference between two numbers."""
    return a - b


def multiply(a, b):
    """Returns the product of two numbers."""
    return a * b


def divide(a, b):
    """Returns the quotient of two numbers, or an error message if b is zero."""
    if b == 0:
        return "Error: Division by zero"
    return a / b


def power(base, exponent=2):
    """Returns base raised to exponent (defaults to 2 for squaring)."""
    return base**exponent


def main():
    while True:
        print("\n--- Calculator Menu ---")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        print("5. Power")
        print("6. Exit")

        choice = input("Choose an operation (1-6): ")

        if choice == "6":
            print("Exiting calculator. Goodbye!")
            break

        if choice in ["1", "2", "3", "4", "5"]:
            num1 = float(input("Enter first number: "))

            if choice == "5":
                exp_input = input(
                    "Enter exponent (leave blank to square by default): "
                )
                if exp_input.strip() == "":
                    result = power(num1)
                else:
                    result = power(num1, float(exp_input))
            else:
                num2 = float(input("Enter second number: "))
                if choice == "1":
                    result = add(num1, num2)
                elif choice == "2":
                    result = subtract(num1, num2)
                elif choice == "3":
                    result = multiply(num1, num2)
                elif choice == "4":
                    result = divide(num1, num2)

            print(f"Result: {result}")
        else:
            print("Invalid choice! Please select 1-6.")


if __name__ == "__main__":
    main()