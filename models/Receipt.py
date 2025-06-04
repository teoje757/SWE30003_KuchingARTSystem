"""Module for generating order receipts."""

import json
import os
from datetime import datetime
import uuid

class Receipt:
    """A class to handle receipt generation for orders."""

    def __init__(self, order):
        """Initialize the Receipt with an order.
        
        Args:
            order (Order): The order to generate receipt for
        """
        self.order = order
        self.receipts_file = "data/receipts.json"

    def request_view_order_details(self):
        """Request order details from the associated order.
        
        Returns:
            dict: The order details dictionary
        """
        return self.order.view_order_details()

    def _save_receipt(self, receipt_data):
        """Save receipt data to receipts.json"""
        try:
            # Load existing receipts
            if os.path.exists(self.receipts_file):
                with open(self.receipts_file, 'r') as f:
                    receipts = json.load(f)
            else:
                receipts = []
            
            # Add new receipt
            receipts.append(receipt_data)
            
            # Save back to file
            with open(self.receipts_file, 'w') as f:
                json.dump(receipts, f, indent=4)
        except Exception as e:
            print(f"⚠️ Could not save receipt: {str(e)}")

    def _format_trip_details(self, trip_bookings):
        """Format trip booking details for receipt"""
        if not trip_bookings:
            return ""
            
        booking = trip_bookings[0]  # Get first booking (assuming one booking per order for simplicity)
        from_station = booking.get('fromStationId', 'Unknown')
        to_station = booking.get('toStationId', 'Unknown')
        fare = booking.get('fare', 0)
        ticket_count = booking.get('ticketCount', 0)
        departure_time = booking.get('departureTime', 'Unknown')
        
        # Try to get route information (you'll need to implement this in TripBooking)
        route_info = ""
        try:
            from models.TripBooking import TripBooking
            tb = TripBooking()
            connection = tb.validate_connection(from_station, to_station)
            if connection:
                if connection["type"] == "direct":
                    route_info = f"ℹ️ Direct trip on {connection['route_name']} route\n"
                else:
                    route_info = (
                        f"ℹ️ Interchange trip:\n"
                        f"  - First leg: {connection['from_route_name']} route\n"
                        f"  - Second leg: {connection['to_route_name']} route\n"
                    )
        except:
            pass
            
        return (
            f"{route_info}"
            f"🚉 From: {from_station} → To: {to_station}\n"
            f"⏰ Departure: {departure_time}\n"
            f"💰 Fare per ticket: RM{fare:.2f}\n"
            f"🎟️ Tickets: {ticket_count} x RM{fare:.2f}\n"
        )

    def generate_receipt(self):
        """Generate and print a formatted receipt for the order."""
        order_details = self.request_view_order_details()
        
        # Create a mapping of payment method values to display names
        payment_display_names = {
            "CREDIT_CARD": "Credit Card",
            "DEBIT_CARD": "Debit Card",
            "PAYPAL": "PayPal",
            "BANK_TRANSFER": "Bank Transfer",
            "CASH_ON_DELIVERY": "Cash On Delivery",
            "E_WALLET": "E-Wallet"
        }

        # Prepare receipt data for saving
        receipt_data = {
            "receipt_id": str(uuid.uuid4()),
            "order_id": order_details['order_id'],
            "user_id": order_details['user_id'],
            "timestamp": datetime.now().isoformat(),
            "items": [],
            "trip_bookings": order_details.get('trip_bookings', []),
            "total_amount": order_details['total_amount'],
            "final_amount": order_details['final_amount'],
            "payment_method": order_details['payment_method'].value if hasattr(order_details['payment_method'], 'value') else order_details['payment_method'],
            "payment_status": order_details['payment_status'],
            "order_status": order_details['order_status'],
            "points_redeemed": order_details.get('points_redeemed', 0)
        }

        print("\n🧾 --- Receipt ---")
        print(f"Order ID: {order_details['order_id']}")
        print(f"User ID: {order_details['user_id']}")
        
        # Handle trip bookings
        if order_details.get('trip_bookings'):
            print("\nTrip Details:")
            print(self._format_trip_details(order_details['trip_bookings']))
            # Add trip bookings to receipt data
            for booking in order_details['trip_bookings']:
                receipt_data['items'].append({
                    'type': 'trip',
                    'description': f"Trip from {booking['fromStationId']} to {booking['toStationId']}",
                    'quantity': booking['ticketCount'],
                    'price': booking['fare'],
                    'total': booking['totalFare']
                })
        # Handle merchandise
        elif order_details.get('items'):
            print("\nItems:")
            for item, quantity in order_details["items"].items():
                price = order_details["merchandise_prices"].get(item, 0)
                print(f"- {item} x {quantity} @ RM{price:.2f} each")
                receipt_data['items'].append({
                    'type': 'merchandise',
                    'description': item,
                    'quantity': quantity,
                    'price': price,
                    'total': quantity * price
                })
        
        print(f"\nTotal Amount: RM{order_details['total_amount']:.2f}")
        print(f"Points Redeemed: {order_details.get('points_redeemed', 0):.1f}")
        print(f"Final Amount: RM{order_details['final_amount']:.2f}")
        
        # Handle payment method display
        payment_method = order_details['payment_method']
        if payment_method:
            if isinstance(payment_method, str):
                print(f"Payment Method: {payment_display_names.get(payment_method, payment_method)}")
            elif hasattr(payment_method, 'value'):
                print(f"Payment Method: {payment_display_names.get(payment_method.value, payment_method.value)}")
        else:
            print("Payment Method: Not specified")
            
        print(f"Payment Status: {order_details['payment_status']}")
        print(f"Order Status: {order_details['order_status']}")
        print("--------------------\n")

        # Save the receipt
        self._save_receipt(receipt_data)