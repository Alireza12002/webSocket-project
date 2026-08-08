from channels.layers import get_channel_layer
from board.settings import CHANNEL_LAYERS
from services.redis_config import redis

class SendHandler():
    channel_layer = get_channel_layer()

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