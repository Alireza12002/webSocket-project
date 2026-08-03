from services.redis_config import redis

class SccoreManager:
    async def correct_guess(self, channel_name, sccore, turn, turn_sccore):
        await redis.set(f"{channel_name}:sccore", sccore)
        await redis.set(f"{turn}:sccore", turn_sccore)

    async def show_sccores(self, channel_name):
        return await redis.get(f"{channel_name}:sccore")
