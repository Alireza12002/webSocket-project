import json

from app.game_manager.match_making import MatchMaker
from channels.generic.websocket import AsyncWebsocketConsumer
from uuid import uuid4


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room = await MatchMaker.join(player=self.channel_name)
        await self.channel_layer.group_add(self.room, self.player)
        await self.game_starter()

    async def disconnect(self, code):
        await MatchMaker.leave(player=self.channel_name, room=self.room)
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def game_starter(self):
        if await redis.scard(self.group) == 4:
            await redis.set(f"{self.group}:round", 0)
            await self.round_manager()
        else:
            return

    async def round_manager(self):
        await redis.incr(f"{self.group}:round")
        self.round_number = int(await redis.get(f"{self.group}:round"))
        await self.start_round()
