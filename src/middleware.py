from aiogram import BaseMiddleware
from aiogram.types import Message
import time
from src.config import BOT_CONFIG

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = None, window: int = None):
        """
        limit: Max messages allowed (defaults to config)
        window: Time window in seconds (defaults to config)
        """
        rl_config = BOT_CONFIG.get("rate_limit", {})
        self.limit = limit if limit is not None else rl_config.get("limit", 2)
        self.window = window if window is not None else rl_config.get("window", 5)

        self.user_requests = {}

    async def __call__(
        self,
        handler,
        event: Message,
        data: dict
    ):
        # Only rate limit messages
        if not isinstance(event, Message):
             return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()

        # Clean up old requests
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Filter timestamps within the window
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if current_time - t < self.window]

        if len(self.user_requests[user_id]) >= self.limit:
            # Drop the request
            return

        self.user_requests[user_id].append(current_time)
        return await handler(event, data)
