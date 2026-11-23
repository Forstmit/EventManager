class EventManagerError(Exception):
    """Базовое исключение приложения."""

class EventNotFoundError(EventManagerError):
    """Мероприятие не найдено."""

class EventCapacityError(EventManagerError):
    """Достигнут лимит участников."""

class InvalidRegistrationError(EventManagerError):
    """Некорректное изменение числа участников."""
