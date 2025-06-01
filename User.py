from trip_booking import start_booking_process
from Order import Order
from Merchandise import Merchandise

def show_main_menu(user):
    username = user["userName"]
    user_id = user["userID"]

    while True:
        print(f"\nWelcome, {username}! How can Kuching ART Online System assist you today?")
        print("1. Book a Trip")
        print("2. Purchase Merchandise")
        print("3. View My Bookings (coming soon)")
        print("4. Redeem Loyalty Points (coming soon)")
        print("5. Logout")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            start_booking_process(user)

        elif choice == '2':
            merch = Merchandise()
            selected_items = merch.promptMerchandiseSelection()

            if not selected_items:
                print("❌ No items selected. Returning to menu.")
                continue

            # Create order ONLY after user selected something
            order = Order(user_id)
            for itemName, quantity, price in selected_items:
                order.requestAddMerchandise(itemName, quantity, price)

            # Continue order processing
            order.calculateTotalAmount()
            order.requestApplyPointsRedemption()
            order.requestSelectPaymentMethod()
            order.requestProcessPayment()

            if order.paymentStatus == "PAID":
                order.submitOrder()
                order.triggerEarnPoints()
                order.processMerchandiseOrder()
                order.requestReceiptGeneration()
                order.requestSendNotification()

                # Save stock and user data only after successful order
                merch.save_merchandise()
                merch.users[str(user_id)]["merchandise"] = merch.users[str(user_id)].get("merchandise", []) + order.merchandiseList
                merch.users[str(user_id)]["merch_spent"] = merch.users[str(user_id)].get("merch_spent", 0) + order.totalAmount
                merch.save_users()
            else:
                print("❌ Order cancelled due to payment failure.")


        elif choice == '3':
            print("Feature coming soon.")

        elif choice == '4':
            print("Feature coming soon.")

        elif choice == '5':
            print("Logging out...")
            break

        else:
            print("Invalid choice. Please try again.")
