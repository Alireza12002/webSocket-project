from services.redis_config import redis
from uuid import uuid4
from .game_manager import GameManager

class MatchMaker():

    async def join(self, player):
        self.player = player

        rooms = await redis.smembers("rooms")

        for room in rooms:
            if await redis.scard(room) < 4:
                group = str(room)
                await redis.sadd(room, self.player)
                return group

        new_room = uuid4().hex
        await redis.sadd("rooms", new_room)
        group = str(new_room)
        await redis.sadd(new_room, self.player)
        if await redis.scard(room) == 4:
            await GameManager.start_game(room)
        return group

    async def leave(self, player, room):
        await redis.srem(room, player)

        if await redis.scard(room) == 0:
            await redis.delete(room)
            await redis.srem("rooms", room)
