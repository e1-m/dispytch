from dispytch import EventBase


class UserNotificationEvent(EventBase):
    __topic__ = "user.{user_id}.notification"
    __event_type__ = "user_notification"

    value: int
    user_id: int
    message: str
