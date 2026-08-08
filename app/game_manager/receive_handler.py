import logging
from app.game_manager.game_manager import GameManager
from app.game_manager.storage import Storage
from services.redis_config import redis

logger = logging.getLogger(__name__)
class ReceiveHandler:
    def __init__(self):
        self.storage = Storage()
        self.gamemanager = GameManager()

    async def handle_message(self, message, channel_layer, player, room):
        if not isinstance(message, dict):
            return

        handlers = {
            "draw": ReceiveHandler.draw,
            "guess": ReceiveHandler.guess,
            "word_choice": ReceiveHandler.word_choice,
        }

        handler = handlers.get(message.get("type"))
        if handler is None:
            return

        await handler(message, channel_layer, player, room)

    async def draw(self, message, channel_layer, player, room):
        if player == await self.storage.get_drawer(room):
            await channel_layer.group_send(room,{"type": "send.drawing", "payload": message})

        logger.info(f"it is not your turn!{player}")
        
    async def guess(self, message, channel_layer, player, room):
        if player == await self.storage.get_drawer():
            logger.warning("you are drawer u cant guess!")
        guess = message.get("text")
        name = await self.storage.get_name(room, player)
        await self.gamemanager.guess_handler(room, guess, name)
     

    async def word_choice(self, message, channel_layer, player, room):
        word = message.get("word")
        await self.storage.set_choosed_word(room, word)
        await self.gamemanager.receive_choice()
