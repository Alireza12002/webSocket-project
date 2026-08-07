from channels.layers import get_channel_layer
from board.settings import CHANNEL_LAYERS
from services.redis_config import redis

class SendHandler():
    channel_layer = get_channel_layer()

    async def active_toolbar(self, player):
        self.channel_layer.send(player, {"type": "activate_toolbar"})

    async def update_players(self, room):
        channel_layer = get_channel_layer()
        players = await redis.smembers(room)
        channel_layer.group_send(room, {"type": "update.players", "players": {"name": "alireza" }})

    async def send_words(self, drawer, words):
        self.channel_layer.send(drawer, {"type": "send.words", "words":words})