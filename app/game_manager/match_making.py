from services.redis_config import redis
from uuid import uuid4
from .game_manager import GameManager

class MatchMaker():
    @staticmethod
    async def join(player):
        player = player

        rooms = await redis.smembers("rooms")

        for room in rooms:
            if await redis.scard(room) < 4:
                
                await redis.sadd(room, player)
                return room

        new_room = uuid4().hex
        await redis.sadd("rooms", new_room)
        group = str(new_room)
        await redis.sadd(new_room, player)
        if await redis.scard(room) == 4:
            await GameManager.start_game(room)
        return new_room
    @staticmethod
    async def leave(player, room):
        await redis.srem(room, player)

        if await redis.scard(room) == 0:
            await redis.delete(room)
            await redis.srem("rooms", room)
