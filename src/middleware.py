from aiogram import BaseMiddleware
from aiogram.types import Message
import time

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 2, window: int = 5):
        """
        limit: Max messages allowed
        window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        # Cache stores list of timestamps for each user_id
        # We use a simple dict for MVP, but cachetools could handle expiry better if needed.
        # Here we just manually prune.
        self.user_requests = {}

    async def __call__(
        self,
        handler,
        event: Message,
        data: dict
    ):
        user_id = event.from_user.id
        current_time = time.time()

        # Clean up old requests
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Filter timestamps within the window
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if current_time - t < self.window]

        if len(self.user_requests[user_id]) >= self.limit:
            # Drop the request (or reply with a warning if desired, but dropping is safer for anti-spam)
            # await event.answer("Слишком много запросов. Пожалуйста, подождите.")
            return

        self.user_requests[user_id].append(current_time)
        return await handler(event, data)
