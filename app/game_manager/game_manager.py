from services.redis_config import redis


class GameManager:
    async def start_game(self, room):
        self.room = room
        await redis.set(f"{room}:round", 1)
        self.round_number = int(await redis.get(f"{room}:round"))
        await self.start_round()

    async def start_round(self):
        pass