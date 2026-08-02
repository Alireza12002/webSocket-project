import json
from channels.generic.websocket import AsyncWebsocketConsumer
from redis.asyncio import Redis
from uuid import uuid4

from app.game_manager.game_manager import GameManager
redis = Redis(host="127.0.0.1", port=6379, db=0, socket_timeout=None)


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.matchmaker()

        await self.accept()
        await self.broadcast_online()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await redis.srem(self.room_name, self.channel_name)
        await self.broadcast_online()

    async def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)

        if json_data["type"] == "draw":
            await self.channel_layer.group_send(
            self.group_name,
            {"type": "send.drawing", "payload": json_data},
        )
        await GameManager.handle_draw(self.channel_layer, json_data)
    async def send_drawing(self, event):
        await self.send(json.dumps(event["payload"]))

    async def broadcast_online(self):
        count = await redis.scard(self.room_name)
        await self.channel_layer.group_send(self.group_name, {"type": "show.online", "count": count})

    async def show_online(self, event):
        count = event["count"]

        await self.send(json.dumps({"type": "online_count", "count": count}))




    async def matchmaker(self):
        self.player = self.channel_name
        rooms = await redis.smembers("rooms")


        for room in rooms:
            if await redis.scard(room) < 4:
                await self.channel_layer.group_add(room, self.player)
                await redis.sadd(room, self.player)
                return 

        new_room = uuid4().hex
        await redis.sadd("rooms", new_room)
        await self.channel_layer.group_add(new_room, self.player)
        await redis.sadd(new_room, self.player)
             
