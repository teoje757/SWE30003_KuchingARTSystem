from models.TripBooking import TripBooking
from models.Order import Order
from models.PaymentAttempt import PaymentAttempt
from models.Merchandise import Merchandise
from models.Notification import Notification
from models.enums import NotificationType
from models.PointsLedger import PointsLedger
from utils.json_handler import load_json, save_json
from datetime import datetime
from datetime import timedelta
import uuid

# In User.py
@staticmethod
def request_cancel_orders(user):
    """Handle order cancellation by delegating to TripBooking"""
    trip_booking = TripBooking()
    trip_booking.process_cancellation(user)

def show_points_balance(user_id):
    """Display the user's current points balance"""
    ledger = PointsLedger()
    points = ledger.get_points(user_id)
    print(f"\n⭐ Your current points balance: {points}")
    print(f"💵 Equivalent value: RM{points:.2f}")

def show_main_menu(user):
    user_name = user["userName"]
    user_id = user["userID"]
    notification = Notification()

    while True:
        # Check for unread notifications (just for the count)
        user_notifications = notification.get_user_notifications(user_id)
        unread_count = sum(1 for n in user_notifications if n["notificationStatus"] == "Unread")
        
        print(f"\nWelcome, {user_name}! How can Kuching ART Online System assist you today?")
        print("1. Trip Booking")
        print("2. Merchandise")
        print("3. My Orders")
        print("4. Loyalty Points")
        print(f"5. Notifications {'✉  ' + str(unread_count) if unread_count > 0 else ''}")
        print("6. Logout")

        choice = input("Enter your choice (1-6): ").strip()

        if choice == '1':
            # Modified to get return values from request_trip_booking
            booking_success, fare, tickets = request_trip_booking(user_id)
            if booking_success:
                # Notification is now handled in the Order.submit_order() method
                pass
            
        elif choice == '2':
            merch = Merchandise()
            selected_items = merch.prompt_merchandise_selection()

            if not selected_items:
                print("❌ No items selected. Returning to menu.")
                continue

            order = Order(user_id)
            for itemName, quantity, price in selected_items:
                order.request_add_merchandise(itemName, quantity, price)

            # Show selected items
            print("\n🧾 Selected Items:")
            for name, quantity, price in selected_items:
                print(f"- {name} x {quantity} @ RM{price:.2f}")

            # Handle points redemption
            if not order.request_apply_points_redemption():
                continue
                
            # Payment processing
            if not order.request_select_payment_method():
                continue
                
            if order.request_process_payment():
                order.submit_order()

                order.process_merchandise_order()
                order.request_receipt_generation()
                
                # Refresh points display
                show_points_balance(user_id)
                # Save merchandise changes
                merch.save_merchandise()
                merch.save_users()
            else:
                print("❌ Order cancelled due to payment failure.")

        elif choice == '3':
            request_cancel_orders(user)
            
        elif choice == '4':
            show_points_balance(user_id)
            notification.create_notification(
                f"Viewed loyalty points balance",
                NotificationType.POINTS_UPDATE,
                "user",
                user_id
            )

        elif choice == '5':
            # View Notifications option
            user_notifications = notification.get_user_notifications(user_id)
            unread_count = sum(1 for n in user_notifications if n["notificationStatus"] == "Unread")
            
            if not user_notifications:
                print("\nYou have no notifications.")
                continue
                
            print(f"\nYou have {len(user_notifications)} notification(s) ({unread_count} unread):")
            for idx, notif in enumerate(user_notifications, 1):
                status = "✓" if notif["notificationStatus"] == "Read" else "✉"
                print(f"{idx}. [{status}] {notif['notificationCreatedTime']} - {notif['notificationContent']}")
            
            mark_read = input("\nMark all as read? (y/n): ").lower()
            if mark_read == 'y':
                data = load_json("data/notifications.json")
                for n in data:
                    if n.get('recipientType') == 'user' and str(user_id) in n.get('recipientUserIds', []):
                        n["notificationStatus"] = "Read"
                save_json("data/notifications.json", data)
                print("All notifications marked as read.")

        elif choice == '6':
            print("Logging out...")
            return

        else:
            print("Invalid choice. Please try again.")
            
def request_trip_booking(user_id):
    """Handle the complete trip booking flow"""
    print("🚌 Book Ticket\n")
    
    trip_booking = TripBooking()
    order = Order(user_id)

    # Get date selection from user
    while True:
        trip_date = input("Enter trip date (YYYY-MM-DD) or leave blank for today: ").strip()
        if not trip_date:
            trip_date = datetime.now().strftime("%Y-%m-%d")
            break
        try:
            parsed_date = datetime.strptime(trip_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            max_date = today + timedelta(days=30)
            
            if parsed_date < today:
                print("❌ Cannot book trips in the past. Please enter a future date.")
                continue
            if parsed_date > max_date:
                print(f"❌ Cannot book trips more than 30 days in advance. Please enter a date before {max_date.strftime('%Y-%m-%d')}.")
                continue
            trip_date = parsed_date.strftime("%Y-%m-%d")  # Ensure consistent format
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD format.")

    stations = trip_booking.get_all_stations()
    if not stations:
        print("❌ No stations available.")
        return False, 0, 0

    print(f"\nAvailable Stations for {trip_date}:")
    for idx, (station_id, station_name) in enumerate(stations, 1):
        print(f"{idx}. {station_id} - {station_name}")

    # Get departure station
    while True:
        from_input = input("\nEnter departure station number: ").strip()
        if from_input.isdigit() and 1 <= int(from_input) <= len(stations):
            from_station = stations[int(from_input)-1][0]
            break
        print("❌ Please enter a valid station number.")

    # Get destination station
    while True:
        to_input = input("Enter destination station number: ").strip()
        if to_input.isdigit() and 1 <= int(to_input) <= len(stations):
            to_station = stations[int(to_input)-1][0]
            if to_station != from_station:
                break
            print("❌ Departure and destination cannot be the same.")
        else:
            print("❌ Please enter a valid station number.")

    # Validate connection
    connection = trip_booking.validate_connection(from_station, to_station)
    if not connection:
        print("❌ These stations are not connected by any route.")
        trip_booking.display_route_map()
        print("ℹ️ Please choose different stations.")
        return False, 0, 0  # Return failure status

    # Find available trips - pass the selected date
    trips = trip_booking.get_trip_details(from_station, trip_date)
    if not trips:
        print(f"❌ No trips found from {from_station} on {trip_date}.")
        return False, 0, 0

    # In the trip display section:
    print(f"\nAvailable Trips on {trip_date}:")
    for idx, trip in enumerate(trips, 1):
        dep_time = trip.get("departureTime", "")
        if "T" in dep_time:  # Full datetime
            # Format as just time for display
            dep_time = datetime.fromisoformat(dep_time).strftime("%H:%M")
        print(f"{idx}. Trip {trip['tripId']} at {dep_time}")

    # Select trip
    while True:
        trip_input = input("Select a trip (1-{}): ".format(len(trips))).strip()
        if trip_input.isdigit() and 1 <= int(trip_input) <= len(trips):
            selected_trip = trips[int(trip_input)-1]
            break
        print("❌ Please enter a valid trip number.")

    # Get ticket count
    while True:
        tickets_input = input("Enter number of tickets: ").strip()
        if tickets_input.isdigit() and int(tickets_input) > 0:
            ticket_count = int(tickets_input)
            break
        print("❌ Please enter a positive number.")

    # Display connection info
    if connection["type"] == "direct":
        print(f"\nℹ️ Direct trip on {connection['route_name']} route")
        print(f"💰 Fare per ticket: RM{connection['fare']:.2f}")
    else:
        print(f"\nℹ️ Interchange trip:")
        print(f"  - First leg: {connection['from_route_name']} route")
        print(f"  - Second leg: {connection['to_route_name']} route")
        print(f"💰 Total fare per ticket: RM{connection['fare']:.2f}")

    print(f"🎟️ Total for {ticket_count} ticket(s): RM{connection['fare'] * ticket_count:.2f}")

    # Create order
    order_id = str(uuid.uuid4())
    order.create_order()
    order.request_add_trip_booking(
        trip_booking_obj=trip_booking,
        from_station=from_station,
        to_station=to_station,
        ticket_count=ticket_count,
        fare_override=connection["fare"],
        trip_date=trip_date,
        departure_time=selected_trip["departureTime"]  # Add this line to pass the selected time
    )

    # Add points redemption option
    if not order.request_apply_points_redemption():
        print("❌ Order cancelled due to points redemption error")
        return False, 0, 0  # Return failure status
    
    # Process payment
    if not order.request_select_payment_method():
        print("❌ Payment method selection cancelled")
        return False, 0, 0  # Return failure status
        
    if order.request_process_payment():
        order.submit_order()
        print("\n✅ Booking confirmed!")
        order.request_receipt_generation()  # Add this line to generate receipt
        return True, connection['fare'], ticket_count  # Return success with fare and ticket count
    else:
        print("\n❌ Payment failed. Please try again.")
        return False, 0, 0  # Return failure status