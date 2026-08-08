from services.redis_config import redis
from uuid import uuid4
from .game_manager import GameManager
from .storage import Storage
class MatchMaker():
    def __init__(self):
        self.storage = Storage()

    async def join(self, channel_name, name):
        rooms = await self.storage.get_rooms()

        for room in rooms:
            players = await self.storage.get_players(room)
            if len(players) < 4:
                await self.storage.add_player_to_the_room(channel_name, room, name)
                return room

        new_room = uuid4().hex
        await self.storage.add_room(new_room)
        await self.storage.init_room(new_room)
        await self.storage.add_player_to_the_room(channel_name, new_room, name)
        
        return new_room
    
    async def leave(self, player, room_name):
        room = await self.storage.get_room(room_name)
        room["players"].pop(player)
        self.storage.save_room(room_name, room)