import logging
from app.game_manager.game_manager import GameManager
from app.game_manager.storage import Storage


logger = logging.getLogger(__name__)
class ReceiveHandler:
    def __init__(self):
        self.storage = Storage()
        self.game_manager = GameManager()

    async def handle_message(self, message, channel_layer, player, room):
        if not isinstance(message, dict):
            return

        handlers = {
            "draw": self.draw,
            "guess": self.guess,
            "word_choice": self.word_choice,
            "clear":self.clear_canvas
        }

        handler = handlers.get(message.get("type"))
        if handler is None:
            return

        await handler(message, channel_layer, player, room)

    async def draw(self, message, channel_layer, player, room):
        if player == await self.storage.get_drawer(room):
            await channel_layer.group_send(room,{"type": "send.drawing", "payload": message})
        else:
            logger.info(f"it is not your turn!{player}")
        
    async def guess(self, message, channel_layer, player, room):# player is the channel_name
        if player == await self.storage.get_drawer(room):
            logger.warning("you are drawer u cant guess!")
            return 
        
        guess = message.get("text")
        name = await self.storage.get_name(room, player)
        await self.game_manager.guess_handler(room, guess, name, player)
     

    async def word_choice(self, message, channel_layer, player, room):
        word = message.get("word")
        await self.storage.set_choosed_word(room, word)
        await self.game_manager.start_draw_handler(room)

    async def clear_canvas(self, message, channel_layer, player, room):
        await self.game_manager.clear_canvas(room, player)
    