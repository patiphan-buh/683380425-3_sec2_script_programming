# main_program.py
import math
import random
import my_utils

# Test greet from custom module
my_utils.greet("Alice")

# Test is_prime from custom module
test_numbers = [7, 10, 13, 20]
for num in test_numbers:
    print(f"Is {num} prime? {my_utils.is_prime(num)}")

# Standard library math module usage
num_to_sqrt = 49
print(f"Square root of {num_to_sqrt}: {math.sqrt(num_to_sqrt)}")

# Standard library random module usage
random_num = random.randint(1, 100)
print(f"Random number between 1 and 100: {random_num}")