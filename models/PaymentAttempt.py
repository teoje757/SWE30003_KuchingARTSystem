"""Module for handling payment attempts and processing."""

import random
from models.enums import PaymentMethod


class PaymentAttempt:
    """A class representing a payment attempt for an order."""

    def __init__(self):
        """Initialize a new payment attempt."""
        self._payment_method = None
        self._payment_status = "PENDING"
        self._amount_to_pay = 0.0

    @property
    def payment_method(self):
        """Get the current payment method."""
        return self._payment_method

    @property
    def payment_status(self):
        """Get the current payment status."""
        return self._payment_status

    def calculate_total_amount(self, order_items):
        """Calculate total amount from order items.
        
        Args:
            order_items (list): List of order items
            
        Returns:
            float: Total amount to pay
        """
        self._amount_to_pay = sum(item["totalPrice"] for item in order_items)
        return self._amount_to_pay

    def select_payment_method(self):
        """Display payment options and handle user selection."""
        print("\n--- Payment Methods ---")
        methods = {
            1: ("Credit Card", PaymentMethod.CREDIT_CARD),
            2: ("Debit Card", PaymentMethod.DEBIT_CARD),
            3: ("PayPal", PaymentMethod.PAYPAL),
            4: ("Bank Transfer", PaymentMethod.BANK_TRANSFER),
            5: ("Cash On Delivery", PaymentMethod.CASH_ON_DELIVERY),
            6: ("E-Wallet", PaymentMethod.E_WALLET)
        }
        
        for num, (display_name, _) in methods.items():
            print(f"{num}. {display_name}")

        print("Type 'cancel' to cancel payment selection.")

        while True:
            choice = input("Select payment method (1-6): ").strip().lower()
            if choice == "cancel":
                print("❌ Payment method selection cancelled.")
                return False

            try:
                choice_num = int(choice)
                if choice_num in methods:
                    self._payment_method = methods[choice_num][1]
                    print(f"✅ Selected: {methods[choice_num][0]}")
                    return True
            except ValueError:
                pass

            print("❌ Invalid choice. Please select a number between 1 and 6 or type 'cancel'.")

    def update_payment_method(self, method):
        """Directly update payment method"""
        self._payment_method = method
        self._payment_attempt.update_payment_method(method)
        print(f"💳 Payment method updated to {method.value.replace('_', '-')}")

    def process_payment(self, amount):
        """Simulate payment processing with 80% success rate.
        
        Args:
            amount (float): The amount to process
            
        Returns:
            bool: True if payment succeeded, False otherwise
        """
        print("\nProcessing payment...")
        self._amount_to_pay = amount
        
        # Simulate payment processing with 80% success rate
        success = random.choices([True, False], weights=[80, 20])[0]
        
        if success:
            self._update_payment_status("PAID")
            print("✅ Payment successful.")
            return True
        
        self._update_payment_status("FAILED")
        print("❌ Payment failed.")
        return False

    def _update_payment_status(self, status):
        """Internal method to update payment status.
        
        Args:
            status (str): New payment status
        """
        self._payment_status = status