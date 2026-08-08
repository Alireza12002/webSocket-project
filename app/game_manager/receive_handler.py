import logging
from app.game_manager.storage import Storage
from services.redis_config import redis

logger = logging.getLogger(__name__)
class ReceiveHandler:
    def __init__(self):
        self.storage = Storage()
    async def handle_message(message, channel_layer, player, room):
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

    async def draw(message, channel_layer, player, room):
        if await redis.get(f"{player}:drawing") == "True":
            await channel_layer.group_send(
                    room,
                    {"type": "send.drawing", "payload": message},
                )
        logger.info(f"it is not your turn!{player}")
        
    async def guess(message, channel_layer, player, room):
        if await redis.get(f"{player}:drawing") == "True":
            logger.warning("you are drawer u cant guess!")
        guess = message.get("text")
        
        await channel_layer.group_send(
            room, {"type": "send.guess", "guess": guess}
        )

    async def word_choice(self, message, channel_layer, player, room):
        word = message.get("word")
        self.storage.set_choosed_word(room, word)
        