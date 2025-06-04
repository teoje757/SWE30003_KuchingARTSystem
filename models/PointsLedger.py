import json
import os

class PointsLedger:
    def __init__(self, ledger_file='data/points_ledger.json'):
        self.ledger_file = ledger_file
        self.ledger = self.load_ledger()

    def load_ledger(self):
        if not os.path.exists(self.ledger_file):
            return {}
        with open(self.ledger_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}

    def save_ledger(self):
        with open(self.ledger_file, 'w') as file:
            json.dump(self.ledger, file, indent=4)

    def get_points(self, userID):
        return self.ledger.get(str(userID), 0)

    def earn_points(self, userID, points_to_earn):
        """Add points to user's balance (1 point per RM10 spent)"""
        try:
            user_id_str = str(userID)
            points = int(points_to_earn)  # Ensure we're working with integers
            
            if points <= 0:
                return 0
                
            current_points = self.ledger.get(user_id_str, 0)
            new_balance = current_points + points
            self.ledger[user_id_str] = new_balance
            self.save_ledger()
            
            print(f"⭐ Points updated: +{points} (New balance: {new_balance})")
            return points
            
        except Exception as e:
            print(f"❌ Error updating points: {str(e)}")
            return 0
        
    def deduct_points(self, userID, amount_to_deduct):
        user_id_str = str(userID)
        current_points = self.ledger.get(user_id_str, 0)

        if current_points < amount_to_deduct:
            print("❌ Not enough points to deduct.")
            return False

        self.ledger[user_id_str] = current_points - int(amount_to_deduct)
        self.save_ledger()
        print(f"🔻 Deducted {int(amount_to_deduct)} points from user {user_id_str}.")
        return True