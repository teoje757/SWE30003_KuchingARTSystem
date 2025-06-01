import uuid
from PaymentAttempt import PaymentAttempt
from PointsLedger import PointsLedger
from Notification import Notification
from Receipt import Receipt

class Order:
    def __init__(self, userID):
        self.userID = userID
        self.orderID = str(uuid.uuid4())
        self.merchandiseList = []  # List of tuples: (itemName, quantity, price)
        self.totalAmount = 0.0
        self.orderFinalAmount = 0.0
        self.paymentMethod = None
        self.paymentStatus = "PENDING"
        self.orderStatus = "CREATED"
        self.pointsLedger = PointsLedger()
        self.paymentAttempt = PaymentAttempt()

    def createOrder(self):
        print(f"📝 Order {self.orderID} created for user {self.userID}.")

    def requestAddMerchandise(self, itemName, quantity, price):
        self.merchandiseList.append((itemName, quantity, price))
        print(f"🛍️ Added {quantity} x {itemName} @ RM{price:.2f} each to the order.")

    def calculateTotalAmount(self):
        self.totalAmount = sum(qty * price for _, qty, price in self.merchandiseList)
        print(f"🧾 Total amount calculated: RM{self.totalAmount:.2f}")
        return self.totalAmount

    def requestApplyPointsRedemption(self):
        current_points = self.pointsLedger.get_points(self.userID)
        print(f"⭐ Current loyalty points: {current_points}")

        if current_points <= 0:
            print("⚠️ You have no loyalty points to redeem.")
            self.orderFinalAmount = self.totalAmount
            return True  # Continue

        use_points = input("Would you like to use your loyalty points? (Y/N, or type 'cancel' to abort): ").strip().lower()
        if use_points == "cancel":
            print("❌ Order cancelled during points redemption.")
            self.orderStatus = "CANCELLED"
            return False

        if use_points != 'y':
            print("ℹ️ Skipping points redemption.")
            self.orderFinalAmount = self.totalAmount
            return True

        redeemable_value = min(current_points, self.totalAmount)
        max_redeemable = max(0, self.totalAmount - 10)  # Enforce RM10 minimum payment rule
        redeem_amount = min(redeemable_value, max_redeemable)

        if redeem_amount > 0:
            success = self.pointsLedger.deductPoints(self.userID, redeem_amount)
            if success:
                print(f"🎁 RM{redeem_amount:.2f} redeemed using loyalty points.")
            else:
                print("⚠️ Points deduction failed.")
        else:
            print("⚠️ You can't redeem points because you must pay at least RM10.")

        self.orderFinalAmount = self.totalAmount - redeem_amount
        print(f"💳 Final amount after redemption: RM{self.orderFinalAmount:.2f}")
        return True

    def requestSelectPaymentMethod(self):
        success = self.paymentAttempt.selectPaymentMethod()
        if success:
            self.updatePaymentMethod(self.paymentAttempt.paymentMethod)
            return True
        else:
            print("❌ Order cancelled during payment method selection.")
            self.orderStatus = "CANCELLED"
            return False


    def updatePaymentMethod(self, method):
        self.paymentMethod = method
        self.paymentAttempt.updatePaymentMethod(method)
        print(f"💳 Payment method updated to {method}.")

    def requestProcessPayment(self):
        max_retries = 3
        attempts = 0

        while attempts < max_retries:
            if not self.requestSelectPaymentMethod():  # << Check cancel
                return  # Exit immediately if cancelled

            if self.orderStatus == "CANCELLED":
                return  # Stop loop if already cancelled

            success = self.paymentAttempt.processPayment(self.orderFinalAmount)

            if success:
                self.updatePaymentStatus("PAID")
                self.orderStatus = "CONFIRMED"
                print(f"✅ Order {self.orderID} confirmed.")
                return
            else:
                self.updatePaymentStatus("FAILED")
                attempts += 1
                print("❌ Payment failed.")

                if attempts >= max_retries:
                    self.orderStatus = "CANCELLED"
                    print("❌ Maximum retry attempts reached. Order cancelled.")
                    return

                choice = input("🔁 Would you like to try another payment method? (Y/N): ").strip().upper()
                if choice != 'Y':
                    self.orderStatus = "CANCELLED"
                    print("❌ Order cancelled by user after failed payment.")
                    return

    def updatePaymentStatus(self, status):
        self.paymentStatus = status
        self.paymentAttempt.updatePaymentStatus(status)

    def submitOrder(self):
        self.updateOrderStatus("CONFIRMED")
        print(f"✅ Order {self.orderID} confirmed.")

    def updateOrderStatus(self, status):
        self.orderStatus = status
        print(f"📦 Order status updated to {status}.")

    def triggerEarnPoints(self):
        self.pointsLedger.earnPoints(self.userID, self.orderFinalAmount)
        print(f"📈 Updated points balance: {self.pointsLedger.get_points(self.userID)}")

    def processMerchandiseOrder(self):
        print("🚚 Processing merchandise order...")

    def requestReceiptGeneration(self):
        receipt = Receipt(self)
        receipt.generateReceipt()

    def viewOrderDetails(self):
        order_summary = {
            "orderID": self.orderID,
            "userID": self.userID,
            "items": {item: qty for item, qty, _ in self.merchandiseList},
            "merchandisePrices": {item: price for item, _, price in self.merchandiseList},
            "totalAmount": self.totalAmount,
            "pointsRedeemed": self.totalAmount - self.orderFinalAmount,
            "orderFinalAmount": self.orderFinalAmount,
            "paymentMethod": self.paymentMethod,
            "paymentStatus": self.paymentStatus,
            "orderStatus": self.orderStatus
        }

        print("--- Order Details ---")
        for k, v in order_summary.items():
            if isinstance(v, dict):
                print(f"{k}:")
                for key, val in v.items():
                    print(f"  {key}: {val}")
            else:
                print(f"{k}: {v}")

        return order_summary

    def requestSendNotification(self):
        notification = Notification()
        notif = notification.createNotification(
            self.userID,
            f"Order {self.orderID} confirmed. Total Paid: RM{self.orderFinalAmount:.2f}"
        )
        notification.sendNotification(notif)
