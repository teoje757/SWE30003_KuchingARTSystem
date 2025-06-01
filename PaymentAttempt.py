class PaymentAttempt:
    def __init__(self):
        self.paymentMethod = None
        self.paymentStatus = "PENDING"
        self.amountToPay = 0.0

    def calculateTotalAmount(self, order_items):
        self.amountToPay = sum(item["totalPrice"] for item in order_items)
        return self.amountToPay

    def selectPaymentMethod(self):
        print("\n--- Payment Methods ---")
        print("1. Credit Card")
        print("2. Debit Card")
        print("3. Paypal")
        print("4. E-Wallet")
        print("5. Cash")
        print("6. QR Code")
        print("Type 'cancel' to cancel payment selection.")

        while True:
            choice = input("Select payment method (1-6): ").strip().lower()
            if choice == "cancel":
                print("❌ Payment method selection cancelled.")
                return False

            methods = {
                "1": "Credit Card",
                "2": "Debit Card",
                "3": "Paypal",
                "4": "E-Wallet",
                "5": "Cash",
                "6": "QR Code"
            }

            self.paymentMethod = methods.get(choice)
            if self.paymentMethod:
                return True
            else:
                print("❌ Invalid choice. Please select a number between 1 and 6 or type 'cancel'.")

    def updatePaymentMethod(self, method):
        self.paymentMethod = method
        print(f"✅ Payment method set to: {self.paymentMethod}")

    def processPayment(self, amount):
        print("\nProcessing payment...")
        self.amountToPay = amount
        import random
        success = random.choices([True, False], weights=[80, 20])[0]
        if success:
            self.updatePaymentStatus("PAID")
            print("✅ Payment successful.")
            return True
        else:
            self.updatePaymentStatus("FAIL")
            print("❌ Payment failed.")
            return False

    def updatePaymentStatus(self, status):
        self.paymentStatus = status
