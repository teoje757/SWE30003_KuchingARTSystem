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

    def earnPoints(self, userID, amount_spent):
        earned = int(amount_spent // 10)  # 1 point per RM10
        user_id_str = str(userID)
        self.ledger[user_id_str] = self.get_points(user_id_str) + earned
        self.save_ledger()
        print(f"🎉 Earned {earned} points for user {user_id_str}.")

    def deductPoints(self, userID, amount_to_deduct):
        user_id_str = str(userID)
        current_points = self.get_points(user_id_str)

        if current_points < amount_to_deduct:
            print("❌ Not enough points to deduct.")
            return False

        self.ledger[user_id_str] = current_points - int(amount_to_deduct)
        self.save_ledger()
        print(f"🔻 Deducted {int(amount_to_deduct)} points from user {user_id_str}.")
        return True
