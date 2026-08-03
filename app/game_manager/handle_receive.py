import logging

from services.redis_config import redis

logger = logging.getLogger(__name__)
class ReceiveHandler:
    @staticmethod
    async def handle_message(message, channel_layer, channel_name, room):
        if not isinstance(message, dict):
            return

        handlers = {
            "draw": ReceiveHandler.draw,
            "guess": ReceiveHandler.guess,
        }

        handler = handlers.get(message.get("type"))
        if handler is None:
            return

        await handler(message, channel_layer, channel_name, room)

    @staticmethod
    async def draw(message, channel_layer, channel_name, room):
        if await redis.get(f"{channel_name}:drawing") == "True":
            await channel_layer.group_send(
                    room,
                    {"type": "send.drawing", "payload": message},
                )
        logger.info(f"it is not your turn!{channel_name}")
    @staticmethod
    async def guess(message, channel_layer, channel_name, room):
        if await redis.get(f"{channel_name}:drawing") == "True":
            logger.warning("you are drawer u cant guess!")
        guess = message.get("text")
        
        await channel_layer.group_send(
            room, {"type": "send.guess", "guess": guess}
        )
