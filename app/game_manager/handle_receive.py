
class ReceiveHandler:
    @staticmethod
    async def handle_message(message, channel_layer, room):
        if not isinstance(message, dict):
            return

        handlers = {
            "draw": ReceiveHandler.draw,
            "guess": ReceiveHandler.guess,
        }

        handler = handlers.get(message.get("type"))
        if handler is None:
            return

        await handler(message, channel_layer, room)

    @staticmethod
    async def draw(message, channel_layer, room):
        await channel_layer.group_send(
                    room,
                    {"type": "send.drawing", "payload": message},
                )

    @staticmethod
    async def guess(message, channel_layer, room):
        guess = message.get("text")
        await channel_layer.group_send(
            room, {"type": "send.guess", "guess": guess}
        )
