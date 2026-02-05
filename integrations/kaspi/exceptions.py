class KaspiAPIError(Exception):
    pass


class KaspiAuthError(KaspiAPIError):
    pass


class KaspiRateLimitError(KaspiAPIError):
    pass
