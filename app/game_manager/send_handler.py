import asyncio
from channels.layers import get_channel_layer
from board.settings import CHANNEL_LAYERS
from app.game_manager.storage import Storage

class SendHandler():
    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def send_players(self, room_name, players):
        # Send to each player individually to avoid race condition with group_add
        # players is a dict {channel_name: player_info}.
        # Each recipient needs its own copy of the list, because the entry that
        # belongs to that recipient must be flagged with "me": True. The client
        # uses that flag to decide whether it is the drawer (see gameroom.js
        # GameUI.players -> setDrawingEnabled). Without it every client thinks
        # it is not the drawer and drawing stays disabled for everyone.
        for channel_name in players:
            players_list = [
                {**info, "me": other_channel == channel_name}
                for other_channel, info in players.items()
            ]
            await self.channel_layer.send(channel_name, {"type":"send_players", "players":players_list})

    async def set_round(self, room_name, round):
        # Send to each player individually to avoid race condition with group_add
        room = await Storage().get_room(room_name)
        if room and "players" in room:
            for channel_name in room["players"]:
                await self.channel_layer.send(channel_name, {"type":"set_round", "round":round})
        else:
            # Fallback to group_send if no room data
            await self.channel_layer.group_send(room_name, {"type":"set_round", "round":round})
        
    async def send_words(self, drawer, words):
        await self.channel_layer.send(drawer, {"type": "send_words", "words":words})

    async def overlay_off(self, player):
        await self.channel_layer.send(player, {"type": "overlay_off"})

    async def turn_on_toolbar(self, drawer):
        await self.channel_layer.send(drawer, {"type": "turn_on_toolbar"})

    async def clear_chat(self, room_name):
        await self.channel_layer.group_send(room_name, {"type":"clear_chat"})

    async def choosed_word(self, player, word, description):
        await self.channel_layer.send(player, {"type":"choosed_word", "description":description, "word":word})

    async def overlay_wait(self, player, text):
        await self.channel_layer.send(player, {"type":"overlay_wait", "text":text})

    async def currect_guess(self, room_name, name):
        await self.channel_layer.group_send(room_name, {"type":"currect_guess", "name":name})

    async def base_chat(self, room_name, name, text):
        await self.channel_layer.group_send(room_name, {"type":"base_chat", "name":name, "text":text})

    async def clear_canvas(self, room_name):
        await self.channel_layer.group_send(room_name, {"type": "clear_canvas"})

    async def score_board(self, room_name, scores: list):
        await self.channel_layer.group_send(room_name, {"type": "score_board", "scores":scores})

    async def round_timer(self, room_name, time):
        await self.channel_layer.group_send(room_name, {"type":"timer", "time":time})

    async def player_joined_chat(self, room_name, name):
        await self.channel_layer.group_send(room_name, {"type":"player_joined", "name":name})

    async def player_leaved_chat(self, room_name, name):
        await self.channel_layer.group_send(room_name, {"type": "player_leaved", "name":name})

    async def player_drawing_chat(self, room_name, drawer_name):
        await self.channel_layer.group_send(room_name, {"type":"player_drawing", "name":drawer_name})