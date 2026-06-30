number = int(input("Enter an integer: "))

if number > 0:
    print("The number is positive.")
elif number < 0:
    print("The number is negative.")
else:
    print("The number is zero.")

if number % 2 == 0:
    print("The number is even.")
else:
    print("The number is odd.")

#Challenge
if number > 0 and number % 2 == 0:
    print("The number is positive and even.")
elif number > 0 and number % 2 != 0:
    print("The number is positive and odd.")
elif number < 0 and number % 2 == 0:
    print("The number is negative and even.")
elif number < 0 and number % 2 != 0:
    print("The number is negative and odd.")
else:
    print("The number is zero.")