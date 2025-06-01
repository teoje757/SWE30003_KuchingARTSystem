# receipt.py

class Receipt:
    def __init__(self, order):
        self.order = order

    def requestViewOrderDetails(self):
        return self.order.viewOrderDetails()

    def generateReceipt(self):
        orderDetails = self.requestViewOrderDetails()

        print("\n🧾 --- Receipt ---")
        print(f"Order ID: {orderDetails['orderID']}")
        print(f"User ID: {orderDetails['userID']}")
        print("Items:")
        for item, quantity in orderDetails["items"].items():
            price = orderDetails["merchandisePrices"].get(item, 0)
            print(f"- {item} x {quantity} @ RM{price:.2f} each")
        print(f"Total Amount: RM{orderDetails['totalAmount']:.2f}")
        print(f"Points Redeemed: {orderDetails['pointsRedeemed']}")
        print(f"Final Amount: RM{orderDetails['orderFinalAmount']:.2f}")
        print(f"Payment Method: {orderDetails['paymentMethod']}")
        print(f"Payment Status: {orderDetails['paymentStatus']}")
        print(f"Order Status: {orderDetails['orderStatus']}")
        print("--------------------\n")
