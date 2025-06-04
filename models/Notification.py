import datetime
import uuid
from utils.json_handler import load_json, save_json
from models.enums import NotificationType  # Updated import

class Notification:
    def create_notification(self, content, notification_type, recipient_type, recipient_id=None):
        """Create a notification for either admin or user.
        
        Args:
            content (str): Notification content
            notification_type (NotificationType): Type of notification
            recipient_type (str): 'user' or 'admin'
            recipient_id (str|list, optional): ID(s) of recipient(s)
            
        Returns:
            dict: Created notification data
        """
        notif = {
            "notificationId": str(uuid.uuid4()),
            "notificationType": notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            "notificationStatus": "Unread",
            "notificationContent": content,
            "notificationCreatedTime": datetime.datetime.now().isoformat(),
            "notificationPublishedTime": datetime.datetime.now().isoformat(),
            "recipientType": recipient_type,
        }
        
        if recipient_id:
            if recipient_type == "user":
                notif["recipientUserIds"] = [recipient_id] if not isinstance(recipient_id, list) else recipient_id
            elif recipient_type == "admin":
                notif["recipientAdminIds"] = [recipient_id] if not isinstance(recipient_id, list) else recipient_id
        
        self.save_notification(notif)
        self.send_notification(notif)
        return notif
    
    def save_notification(self, notif):
        data = load_json("data/notifications.json")
        data.append(notif)
        save_json("data/notifications.json", data)

    def send_notification(self, notif):
        print("\n[Notification Sent]")
        print(f"Type: {notif['notificationType']}")
        print(f"Content: {notif['notificationContent']}")
        
        if notif.get('recipientUserIds'):
            print(f"Recipients: {len(notif['recipientUserIds'])} users")
        elif notif.get('recipientAdminIds'):
            print("Recipient: System Administrators")
        elif notif.get('recipientType') == 'admin':
            print("Recipient: All Administrators")
            
    def get_user_notifications(self, user_id):
        data = load_json("data/notifications.json")
        return [n for n in data if n.get('recipientType') == 'user' and str(user_id) in n.get('recipientUserIds', [])]
    
    def get_admin_notifications(self, admin_id=None):
        data = load_json("data/notifications.json")
        if admin_id:
            return [n for n in data if n.get('recipientType') == 'admin' and str(admin_id) in n.get('recipientAdminIds', [])]
        return [n for n in data if n.get('recipientType') == 'admin']