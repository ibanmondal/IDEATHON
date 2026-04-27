from slowapi import Limiter
from slowapi.util import get_remote_address

# Global rate limiter using the remote address of the request
limiter = Limiter(key_func=get_remote_address)
