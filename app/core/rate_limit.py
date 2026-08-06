"""
AgroAI — Rate Limiting
Configures SlowAPI-based rate limiting for sensitive endpoints.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
