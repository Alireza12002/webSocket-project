from services.redis_config import redis
from uuid import uuid4
from .game_manager import GameManager
from .storage import Storage
class MatchMaker():
    @staticmethod
    async def join(channel_name, name):
        channel_name = channel_name
        storage = Storage()
        rooms = storage.get_rooms()

        for room in rooms:
            if len(storage.get_players(room)) > 4:
                await storage.add_player_to_the_room(channel_name, room, name)
                return room

        new_room = uuid4().hex
        storage.add_room(new_room)
        await storage.add_player_to_the_room(channel_name, room, name)
        Storage.init_room(new_room)
        return new_room
    @staticmethod
    async def leave(player, room):
        await redis.srem(room, player)

        if await redis.scard(room) == 0:
            await redis.delete(room)
            await redis.srem("rooms", room)
