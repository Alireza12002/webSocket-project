import json
import logging
from app.game_manager.receive_handler import ReceiveHandler
from app.game_manager.game_manager import GameManager
from app.game_manager.match_making import MatchMaker
from channels.generic.websocket import AsyncWebsocketConsumer
from app.game_manager.storage import Storage
logger = logging.Logger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.match_maker = MatchMaker()
        self.game_manager = GameManager()
        self.receive_handler = ReceiveHandler()
    async def connect(self):
        await self.accept()
        player_name = self.scope["session"].get("username")
        self.room = await self.match_maker.join(self.channel_name, player_name)
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.game_manager.join_handler(self.room)

    async def disconnect(self, code):# need to work  
        await self.channel_layer.group_discard(self.room, self.channel_name)
        await self.match_maker.leave(player=self.channel_name, room_name=self.room)
    async def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        await self.receive_handler.handle_message(json_data, self.channel_layer, self.channel_name, self.room)

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

    async def currect_guess(self, event):
        await self.send(json.dumps({"type": "ui", "action":"chat_add", "name":event["name"], "text":f"{event["name"]} guessed correctly!", "chatType":"guessed"}))

    async def base_chat(self, event):
        await self.send(json.dumps({"type":"ui", "action":"chat_add", "name":event["name"],"text":event["text"], "chatType":"base"}))

    async def send_players(self, event):
        await self.send(json.dumps({"type":"ui", "action":"players", "payload":event["players"]}))

    async def set_round(self, event):
        await self.send(json.dumps({"type":"ui", "action":"round", "text":f"round {event["round"]} of 3"}))