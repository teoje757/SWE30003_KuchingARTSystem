import json
import os

MERCHANDISE_FILE = "data/merchandise.json"
USERS_FILE = "data/users.json"


class Merchandise:
    def __init__(self):
        self.users = self.load_users()
        raw_list = self.load_merchandise()
        self.merchandise = {item["merchandiseName"]: item for item in raw_list}

    def load_merchandise(self):
        if not os.path.exists(MERCHANDISE_FILE):
            return []
        with open(MERCHANDISE_FILE, "r") as f:
            return json.load(f)

    def save_merchandise(self):
        with open(MERCHANDISE_FILE, "w") as f:
            json.dump(list(self.merchandise.values()), f, indent=4)

    def load_users(self):
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    def save_users(self):
        with open(USERS_FILE, "w") as f:
            json.dump(self.users, f, indent=4)

    def prompt_merchandise_selection(self):
        print("\n🛍️ Available Merchandise:")
        for idx, (name, item) in enumerate(self.merchandise.items(), start=1):
            stock = item["merchandiseStock"]
            price = item["merchandisePrice"]
            stock_display = "⚠️ Low stock!" if stock < 10 else ""
            print(f"{idx}. {name} (RM{price:.2f}) {stock_display}")

        selected_items = []
        while True:
            choice = input(
                "Enter the item number to buy (or 'done' to finish, 'cancel' to abort): "
            ).strip().lower()
            if choice == "cancel":
                print("❌ Order cancelled. Returning to main menu...")
                return []
            if choice == "done":
                break
            if not choice.isdigit() or int(choice) not in range(1, len(self.merchandise) + 1):
                print("❌ Invalid selection. Try again.")
                continue

            idx = int(choice) - 1
            item_name = list(self.merchandise.keys())[idx]
            item_data = self.merchandise[item_name]
            stock = item_data["merchandiseStock"]
            price = item_data["merchandisePrice"]

            qty_input = input(
                f"How many '{item_name}' would you like to buy? (type 'cancel' to go back): "
            ).strip().lower()
            if qty_input == "cancel":
                print("🔙 Returning to merchandise selection...")
                continue
            if not qty_input.isdigit():
                print("❌ Please enter a valid number.")
                continue

            quantity = int(qty_input)
            if quantity <= 0:
                print("❌ Quantity must be greater than 0.")
                continue
            if quantity > stock:
                print(f"❌ Not enough stock. Only {stock} available.")
                continue

            selected_items.append((item_name, quantity, price))
            # Reserve stock
            self.merchandise[item_name]["merchandiseStock"] -= quantity

        return selected_items