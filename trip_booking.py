import json

USER_FILE = 'data/users.json'

def save_user_changes(updated_user):
    # Load users dictionary (keyed by userID as string)
    with open(USER_FILE, 'r') as f:
        users = json.load(f)

    # Update the user data by userID string key
    user_key = str(updated_user['userID'])
    users[user_key] = updated_user

    # Save back to file
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def start_booking_process(user):
    print("\n--- Trip Booking ---")

    trips = ["Trip A - Station 1 to Station 3", "Trip B - Station 2 to Station 4"]
    for idx, trip in enumerate(trips, 1):
        print(f"{idx}. {trip}")

    try:
        trip_choice = int(input("Select a trip by number: ")) - 1
        selected_trip = trips[trip_choice]
    except (IndexError, ValueError):
        print("Invalid trip selection.")
        return

    base_price = 10.00
    print(f"\nTrip selected: {selected_trip}")
    print(f"Base price: RM {base_price:.2f}")

    use_points = input("Apply loyalty points? (yes/no): ").lower()
    discount = 2.00 if use_points == 'yes' and user.get('loyalty_points', 0) >= 20 else 0.00
    total_due = base_price - discount
    print(f"Discount applied: RM {discount:.2f}")
    print(f"Total due: RM {total_due:.2f}")

    for attempt in range(1, 3):
        print(f"\nPayment Attempt {attempt}")
        payment = input("Enter 'pay' to simulate payment: ")
        if payment.lower() == 'pay':
            print("Payment successful!")
            break
        else:
            print("Payment failed.")
            if attempt == 2:
                print("All payment attempts failed. Try again later.")
                return

    if "trips" not in user:
        user["trips"] = []

    user["trips"].append(selected_trip)

    # Deduct loyalty points if used
    if discount > 0:
        user['loyalty_points'] -= 20  # assume 20 points required for discount

    # Add loyalty points for this booking
    user['loyalty_points'] = user.get('loyalty_points', 0) + 10

    save_user_changes(user)

    print("\nBooking confirmed! Ticket generated.")
