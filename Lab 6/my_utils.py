# my_utils.py
def greet(name):
    """Prints a friendly greeting message."""
    print(f"Hello, {name}!")


def is_prime(number):
    """Returns True if the number is prime, False otherwise."""
    if number <= 1:
        return False
    for i in range(2, int(number**0.5) + 1):
        if number % i == 0:
            return False
    return True