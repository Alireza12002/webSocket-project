import json
from pydoc import text
from app.game_manager.handle_receive import ReceiveHandler
from app.game_manager.game_manager import GameManager
from app.game_manager.match_making import MatchMaker
from channels.generic.websocket import AsyncWebsocketConsumer
from uuid import uuid4


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.room = await MatchMaker.join(player=self.channel_name)
        await self.channel_layer.group_add(self.room, self.channel_name)
        game = GameManager()
        await game.start_game(self.room)

    async def disconnect(self, code):
        await MatchMaker.leave(player=self.channel_name, room=self.room)
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        await ReceiveHandler.handle_message(json_data, self.channel_layer, self.channel_name, self.room)


    async def send_drawing(self, event):
        await self.send(json.dumps({"type":"draw", "payload":event["payload"]}))

    async def send_guess(self, event):
        await self.send(json.dumps({"type":"ui", "action":"chat_add", "name":"ali", "text": event["guess"], "chat_type": "base"}))