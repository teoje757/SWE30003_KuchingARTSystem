# models/Order.py
"""Module for handling order creation and management."""

import uuid
import json
import os
from datetime import datetime
from models.PaymentAttempt import PaymentAttempt
from models.PointsLedger import PointsLedger
from models.Notification import Notification
from models.enums import NotificationType
from models.Receipt import Receipt
from models.enums import TripBookingStatus
from models.enums import OrderStatus

ORDERS_FILE = "data/orders.json"

class Order:
    """A class representing a customer order with payment processing."""

    def __init__(self, user_id):
        """Initialize a new order."""
        self._user_id = user_id
        self._order_id = str(uuid.uuid4())
        self._merchandise_list = []
        self._trip_bookings = []
        self._total_amount = 0.0
        self._final_amount = 0.0
        self._payment_method = None
        self._payment_status = "PENDING"
        self._order_status = "CREATED"
        self._points_ledger = PointsLedger()
        self._payment_attempt = PaymentAttempt()
        self._notification = Notification()
        self._points_redeemed = 0.0

    def create_order(self):
        """Initialize a new order."""
        print(f"📝 Order {self._order_id} created for user {self._user_id}.")

    def request_add_trip_booking(self, trip_booking_obj, from_station, to_station, ticket_count, fare_override, trip_date, departure_time=None):
        """Add a trip booking to the order"""
        trips = trip_booking_obj.get_trip_details(from_station, trip_date)
        if not trips:
            print("❌ No available trips found.")
            return False

        # Find the trip that matches the selected departure time
        selected_trip = None
        if departure_time:
            for trip in trips:
                if trip.get("departureTime") == departure_time:
                    selected_trip = trip
                    break
        
        # If no matching trip found or no departure_time provided, use the first trip
        if not selected_trip:
            selected_trip = trips[0]
            print("⚠️ Using first available trip as fallback")

        # Use fare_override if provided, otherwise use trip fare
        fare = fare_override if fare_override is not None else float(selected_trip.get("fare", 0))
        total_fare = fare * ticket_count

        trip_booking = {
            "tripBookingId": str(uuid.uuid4()),
            "tripId": selected_trip["tripId"],
            "userId": self._user_id,
            "orderId": self._order_id,
            "fromStationId": from_station,
            "toStationId": to_station,
            "departureTime": selected_trip["departureTime"],  # Use the selected trip's time
            "fare": fare,
            "ticketCount": ticket_count,
            "totalFare": total_fare,
            "bookingStatus": TripBookingStatus.REQUESTED.value
        }

        self._trip_bookings.append(trip_booking)
        self._total_amount = total_fare  # Set total amount for trip bookings
        self._final_amount = total_fare
        print(f"🎟️ Added {ticket_count} ticket(s) from {from_station} to {to_station}")
        print(f"⏰ Departure Time: {selected_trip['departureTime']}")  # Debug print
        return True
        
    def request_add_merchandise(self, item_name, quantity, price):
        """Add item to order with validation.
        
        Args:
            item_name (str): Name of the item
            quantity (int): Quantity to order
            price (float): Price per unit
        """
        self._validate_merchandise(item_name, quantity, price)
        self._merchandise_list.append((item_name, quantity, price))
        self.calculate_total_amount()
        print(f"🛍️ Added {quantity} x {item_name} @ RM{price:.2f}")

    def calculate_total_amount(self):
        """Calculate and return order total"""
        self._total_amount = sum(qty * price for _, qty, price in self._merchandise_list)
        self._final_amount = self._total_amount  # Reset final amount
        return self._total_amount
    
    def request_apply_points_redemption(self):
        """Handle points redemption flow"""
        if not self._validate_redemption_conditions():
            return False
        
        points = self._points_ledger.get_points(self._user_id)
        
        if points <= 0:
            print("⚠️ No points available to redeem.")
            return True  # Continue with order without points
        
        print(f"⭐ Available points: {points}")
        choice = input("Use points? (Y/N/cancel): ").strip().lower()
        
        if choice == "cancel":
            print("❌ Redemption cancelled")
            return False
        if choice != "y":
            return True  # Continue with order without using points
            
        redeem_amount = self._calculate_redeemable_amount(points)
        if redeem_amount > 0:
            if self._points_ledger.deduct_points(self._user_id, redeem_amount):
                self._points_redeemed = redeem_amount
                self._final_amount = max(0, self._total_amount - redeem_amount)
                print(f"💰 Redeemed {redeem_amount} points. New total: RM{self._final_amount:.2f}")
        return True

    def request_select_payment_method(self):
        """Handle payment method selection"""
        if self._payment_attempt.select_payment_method():
            self._payment_method = self._payment_attempt.payment_method
            # Create a mapping for display names
            payment_names = {
                "CREDIT_CARD": "Credit Card",
                "DEBIT_CARD": "Debit Card",
                "PAYPAL": "PayPal",
                "BANK_TRANSFER": "Bank Transfer",
                "CASH_ON_DELIVERY": "Cash On Delivery",
                "E_WALLET": "E-Wallet"
            }
            display_name = payment_names.get(self._payment_method.value, self._payment_method.value)
            print(f"💳 Payment method set to {display_name}")
            return True
        print("❌ Payment method selection cancelled")
        return False

    def update_payment_method(self, method):
        """Directly update payment method"""
        self._payment_method = method
        self._payment_attempt.update_payment_method(method)
        display_name = {
            "CREDIT_CARD": "Credit Card",
            "DEBIT_CARD": "Debit Card",
            "PAYPAL": "PayPal",
            "BANK_TRANSFER": "Bank Transfer",
            "CASH_ON_DELIVERY": "Cash On Delivery",
            "E_WALLET": "E-Wallet"
        }.get(method.value, method.value)
        print(f"💳 Payment method set to {display_name}")

    def request_process_payment(self):
        """Handle payment processing"""
        for attempt in range(3):
            if not self._payment_method and not self.request_select_payment_method():
                return False
                
            if self._process_payment_attempt():
                return True
                
            if not self._handle_payment_failure(attempt):
                return False
                
        return False

    def update_payment_status(self, status):
        """Update payment status"""
        self._payment_status = status
        self._payment_attempt._update_payment_status(status)
        print(f"🔄 Payment status updated to {status}")

    # In Order.py, modify the submit_order method
    def submit_order(self):
        """Finalize and submit order"""
        if not self._validate_submission():
            return False
            
        # Update all trip bookings to COMPLETED status
        for booking in self._trip_bookings:
            booking["bookingStatus"] = TripBookingStatus.CONFIRMED.value
        
        self.update_order_status(OrderStatus.CONFIRMED.value)
        self.save_to_orders_file()
        
        # Calculate points based on FINAL amount (RM10 = 1 point)
        try:
            final_amount = float(self._final_amount)
            points_earned = int(final_amount // 10)
            
            if points_earned > 0:
                actual_earned = self._points_ledger.earn_points(self._user_id, points_earned)
                print(f"🎉 Earned {actual_earned} points for this purchase!")
            else:
                print(f"ℹ️ No points earned (minimum RM10 needed, spent RM{final_amount:.2f})")
        except Exception as e:
            print(f"⚠️ Points calculation error: {str(e)}")
        
        # Send appropriate notifications based on order type
        if self._trip_bookings and self._merchandise_list:
            # Combined order (both trips and merchandise)
            message = f"Order #{self._order_id} confirmed. Includes {len(self._trip_bookings)} trip(s) and {len(self._merchandise_list)} item(s). Total: RM{self._final_amount:.2f}"
            notification_type = NotificationType.ORDER_UPDATE
        elif self._trip_bookings:
            # Trip booking only
            message = f"Trip booking confirmed. Total paid: RM{self._final_amount:.2f}"
            notification_type = NotificationType.BOOKING_CONFIRMATION
        elif self._merchandise_list:
            # Merchandise only
            message = f"Merchandise order #{self._order_id} confirmed. Total: RM{self._final_amount:.2f}"
            notification_type = NotificationType.ORDER_UPDATE
        else:
            # Empty order (shouldn't happen due to validation)
            message = f"Order #{self._order_id} confirmed"
            notification_type = NotificationType.ORDER_UPDATE
        
        self._notification.create_notification(
            message,
            notification_type,
            "user",
            self._user_id
        )
        
        print("✉️ Notification sent")
        print(f"✅ Order {self._order_id} submitted")
        return True
    
    def update_order_status(self, status):
        """Update order status"""
        self._order_status = status
        print(f"📦 Status updated to {status}")
    
    def process_merchandise_order(self):
        """Process order fulfillment"""
        print("🚚 Processing merchandise order...")

    def request_receipt_generation(self):
        """Generate order receipt"""
        receipt = Receipt(self)
        receipt.generate_receipt()
        print("🧾 Receipt generated")

    def view_order_details(self):
        """Display order summary.
        
        Returns:
            dict: Dictionary containing order details
        """
        return {
            "order_id": self._order_id,
            "user_id": self._user_id,
            "items": dict(
                (item[0], item[1]) for item in self._merchandise_list
            ),
            "merchandise_prices": dict(
                (item[0], item[2]) for item in self._merchandise_list
            ),
            "trip_bookings": self._trip_bookings,
            "total_amount": self._total_amount,
            "final_amount": self._final_amount,
            "payment_method": self._payment_method,
            "payment_status": self._payment_status,
            "order_status": self._order_status,
            "points_redeemed": self._points_redeemed
        }

    def save_to_orders_file(self):
        """Save order to file"""
        order_data = self._prepare_order_data()
        
        try:
            # Save to orders.json
            existing = self._load_existing_orders()
            if self._user_id not in existing:
                existing[self._user_id] = {"orders": []}
            existing[self._user_id]["orders"].append(order_data)
            
            with open(ORDERS_FILE, "w") as f:
                json.dump(existing, f, indent=4)
            
            # Save trip bookings to tripbookings.json if they exist
            if self._trip_bookings:
                self._save_trip_bookings()
            
            return True
        except Exception as e:
            print(f"❌ Failed to save order: {str(e)}")
            return False

    def _save_trip_bookings(self):
        """Save trip bookings to separate file"""
        trips_file = "data/tripbookings.json"
        try:
            # Load existing trips
            existing_trips = {}
            if os.path.exists(trips_file):
                with open(trips_file, "r") as f:
                    existing_trips = json.load(f)
            
            # Initialize user's trip bookings if not exists
            if self._user_id not in existing_trips:
                existing_trips[self._user_id] = []
            
            # Add new trip bookings
            existing_trips[self._user_id].extend(self._trip_bookings)
            
            # Save back to file
            with open(trips_file, "w") as f:
                json.dump(existing_trips, f, indent=4)
                
        except Exception as e:
            print(f"⚠️ Warning: Could not save trip bookings: {str(e)}")

    # Protected helper methods
    def _validate_merchandise(self, item_name, quantity, price):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price < 0:
            raise ValueError("Price cannot be negative")

    def _validate_redemption_conditions(self):
        if self._order_status == "CANCELLED":
            print("❌ Order is cancelled")
            return False
        if not self._merchandise_list and not self._trip_bookings:
            print("❌ No items in order")
            return False
        return True

    def _calculate_redeemable_amount(self, available_points):
        redeemable = min(available_points, self._total_amount)
        return redeemable

    def _process_payment_attempt(self):
        """Process a payment attempt using the payment attempt object."""
        if self._payment_attempt.process_payment(self._final_amount):
            self.update_payment_status("PAID")
            return True
        self.update_payment_status("FAILED")
        return False
    
    def _handle_payment_failure(self, attempt):
        if attempt >= 2:
            print("❌ Max attempts reached")
            return False
            
        choice = input("Retry with new method? (Y/N): ").upper()
        if choice != "Y":
            return False
            
        self._payment_method = None
        return True

    def _validate_submission(self):
        if self._payment_status != "PAID":
            print("❌ Order must be paid first")
            return False
        return True

    def _prepare_order_data(self):
        return {
            "order_id": self._order_id,
            "user_id": self._user_id,
            "trip_bookings": self._trip_bookings,
            "items": self._merchandise_list,
            "total": self._total_amount,
            "final_amount": self._final_amount,
            "payment_method": self._payment_method.value if self._payment_method else None,
            "status": self._order_status,
            "timestamp": datetime.now().isoformat(),
            "points_redeemed": self._points_redeemed
        }

    def _load_existing_orders(self):
        if not os.path.exists(ORDERS_FILE):
            return {}
            
        try:
            with open(ORDERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def get_active_trip_bookings(self):
        """Retrieve all trip bookings for this user (including cancelled ones)"""
        if not os.path.exists("data/orders.json"):
            return []

        with open("data/orders.json", "r") as f:
            all_orders = json.load(f)

        user_orders = all_orders.get(str(self._user_id), {}).get("orders", [])
        if not user_orders:
            return []

        all_trip_bookings = []
        for order in user_orders:
            if "trip_bookings" in order:
                all_trip_bookings.extend(order["trip_bookings"])

        return all_trip_bookings  # Return all bookings, not just active ones

    def cancel_trip_booking(self, booking_id, dep_datetime):
        """Cancel a specific trip booking and update order status"""
        # Load existing orders
        with open("data/orders.json", "r") as f:
            all_orders = json.load(f)

        user_orders = all_orders.get(str(self._user_id), {}).get("orders", [])
        
        # Update booking and order status
        for order in user_orders:
            if "trip_bookings" in order:
                for booking in order["trip_bookings"]:
                    if booking["tripBookingId"] == booking_id:
                        booking["bookingStatus"] = TripBookingStatus.CANCELLED.value
                        order["status"] = (
                            OrderStatus.REFUNDED.value 
                            if (dep_datetime - datetime.now()).total_seconds() > 86400
                            else OrderStatus.REFUNDED_FAIL.value
                        )
                        break

        # Save changes
        with open("data/orders.json", "w") as f:
            json.dump(all_orders, f, indent=4)