from fastapi import status

from base_exceptions import BaseAppError


class ProxyProcessingError(BaseAppError):
    def __init__(self,
                 status_: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
                 details: str = "Error during processing your request with proxy endpoint"):
        super().__init__(status_, details)


class NoProxiesError(ProxyProcessingError):
    def __init__(self):
        super().__init__(details="No proxies was sent")


class ProxySearchQueryError(ProxyProcessingError):
    def __init__(self, details="Search query error"):
        super().__init__(details=details)


class NoFormatStringError(ProxySearchQueryError):
    def __init__(self):
        super().__init__(details="Custom format option is set, but format_string is empty")


class UnknownFormatType(ProxySearchQueryError):
    def __init__(self):
        super().__init__(details="Unknown format_type It can be 'url', 'norma' or 'custom'")


class CheckIsRunningError(ProxyProcessingError):
    def __init__(self):
        super().__init__(details="You cannot purge database during active check.")

