from enum import Enum

class AuthenticationServiceStatus(Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    LOCKED = "Locked"

class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    E_WALLET = "E_WALLET"

class TripStatus(Enum):
    SCHEDULED = "Scheduled"
    STARTED = "Started"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    RESCHEDULED = "Rescheduled"

class NotificationType(Enum):
    BOOKING_CONFIRMATION = "Booking_confirmation"
    ORDER_UPDATE = "Order_update"
    REFUND_STATUS = "Refund_status"
    SYSTEM_ALERT = "System_alert"
    POINTS_UPDATE = "Points_update"
    PROMOTION = "Promotion"
    USER_NOTIFICATION = "User_Notification"

class TripBookingStatus(Enum):
    REQUESTED = "Requested"
    CONFIRMED = "Confirmed"
    RESCHEDULE_REQUESTED = "Reschedule_requested"
    RESCHEDULED = "Rescheduled"
    RESCHEDULED_FAIL = "Rescheduled_fail"
    CANCELLED = "Cancelled"
    CANCELLATION_REQUESTED = "Cancellation_requested"

class OrderStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    REFUNDED = "Refunded"
    REFUNDED_FAIL = "Refunded_Fail"
    REFUND_REQUESTED = "Refund_Requested"  # New status
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    CANCELLATION_FAIL = "Cancellation_Fail"