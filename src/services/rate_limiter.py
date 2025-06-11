class LoginRateLimiter:
    def __init__(self, redis):
        self.redis = redis
        self.max_attempts = 5
        self.block_seconds = 600

    @staticmethod
    def _fail_key(user_email: str) -> str:
        return f"failed_login:{user_email}"

    @staticmethod
    def _block_key(user_email: str) -> str:
        return f"blocked_user:{user_email}"

    async def is_blocked(self, user_email: str) -> bool:
        return await self.redis.exists(self._block_key(user_email))

    async def incr_attempts(self, user_email: str) -> int:
        key = self._fail_key(user_email)
        attempts = await self.redis.incr(key)
        if attempts == 1:
            await self.redis.expire(key, self.block_seconds)
        if attempts >= self.max_attempts:
            await self.redis.set(self._block_key(user_email), "1", ex=self.block_seconds)
            await self.redis.delete(key)
        return attempts

    async def reset_attempts(self, user_email: str):
        await self.redis.delete(self._fail_key(user_email))
