from channels.layers import get_channel_layer
from board.settings import CHANNEL_LAYERS
from app.game_manager.storage import Storage

class SendHandler():
    channel_layer = get_channel_layer()

    async def send_players(self, room_name, players):
        # Send to each player individually to avoid race condition with group_add
        # players is a dict {channel_name: player_info}, extract values for the UI
        players_list = list(players.values())
        for channel_name in players:
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