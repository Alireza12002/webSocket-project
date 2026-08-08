import json
import logging
from app.game_manager.receive_handler import ReceiveHandler
from app.game_manager.game_manager import GameManager
from app.game_manager.match_making import MatchMaker
from channels.generic.websocket import AsyncWebsocketConsumer
from app.game_manager.storage import Storage
logger = logging.Logger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        player_name = self.scope["session"].get("username")
        self.room = await MatchMaker.join(self.channel_name, player_name)
        await self.channel_layer.group_add(self.room, self.channel_name)
        game_manager = GameManager()
        await game_manager.join_handler(self.room)

    async def disconnect(self, code):
        await MatchMaker.leave(player=self.player, room=self.room)
        await self.channel_layer.group_discard(self.room, self.player)

    async def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        await ReceiveHandler.handle_message(json_data, self.channel_layer, self.player, self.room)

    async def send_drawing(self, event):
        await self.send(json.dumps({"type":"draw", "payload":event["payload"]}))

    async def send_guess(self, event):
        await self.send(json.dumps({"type":"ui", "action":"chat_add", "name":"ali", "text": event["guess"], "chat_type": "base"}))

    async def activate_toolbar(self):
        await self.send(json.dumps({"type": "ui", "action": "toolbar", "visible":True}))

    async def send_words(self, event):
        await self.send(json.dumps({"type":"ui", "action":"overlay", "show":True, "mode":"words", "words":event["words"]}))

    async def overlay_off(self):
        await self.send(json.dumps({"type":"ui", "action":"overlay", "show":False}))

    async def turn_on_toolbar(self):
        await self.send(json.dumps({"type":"ui", "action":"toolbar", "visible":True}))

    async def clear_chat(self):
        await self.send(json.dumps({"type":"ui", "action":"clear_chat"}))

    async def choosed_word(self, event):
        await self.send(json.dumps({"type":"ui", "action":"word", "description": event["description"], "word":event["word"]}))

    async def overlay_wait(self, event):
        await self.send(json.dumps({"type":"ui", "action":"overlay", "show": True, "mode": "text", "text":event["text"]}))