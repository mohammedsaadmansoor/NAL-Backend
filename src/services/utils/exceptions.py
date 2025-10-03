class APIException(Exception):
    def __init__(self, message: str, error_code: str | None = None, details: dict | None = None, status_code: int = 500):
        self.message = message.lower()
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "status_code": self.status_code
        }
