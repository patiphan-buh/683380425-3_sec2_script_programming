age = int(input("Enter your age: "))

if age < 5:
    print("You're too young for movies! Enjoy cartoons.")

elif age <= 12:
    print("Recommended: G-rated or PG-rated movies.")

elif age <= 17:
    print("Recommended: PG-13 or R-rated (with parental guidance).")

else:
    print("Recommended: Any movie rating.")

    # Challenge)
    like_action = input("Do you like action movies? (yes/no): ").lower()

    if age >= 18 and like_action == "yes":
        print("You might enjoy the latest action blockbuster!")