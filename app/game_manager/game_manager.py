from app.game_manager.send_handler import SendManager
from app.game_manager.storage import Storage
from services.redis_config import redis
import random
import json
class GameManager:
    words = ["Apple", "Bicycle", "Cactus", "Diamond", "Envelope",
             "Feather", "Guitar", "Helmet", "Igloo", "Jacket", "Map",
             "Alligator", "Bear", "Butterfly", "Cloud", "Dolphin",
             "Elephant", "Flower", "Giraffe", "Honeybee", "Island"
             "Banana", "Cake", "Door", "Egg", "Fork", "Glass", "Ring",
             "House", "Ice cream", "Kettle", "Anchor", "Bridge",
             "Castle", "Desert", "Elevator", "Forest", "Garden",
             "Harbor", "Ladder", "Mountain", "Balloon", "Camera",
             "Drum", "Kite", "Lamp",  "Pencil",  "Telescope", "Umbrella"
             ]
    def __init__(self):
        self.storage = Storage
    async def join_handler(self, room):
        if len(await self.storage.get_players(room)) == 4:
            await self.start_game(room)

    async def start_game(self, room_name):
        self.room_name = room_name
        await self.init_jobs()
        await self.start_round()

    async def start_round(self):
        room = self.storage.get_room(self.room_name)
        if room["round"] == 4:
            return # show sccores
        room["round"] += 1
        self.turn = self.player_turn_manager() #make a new turn system
        room["drawer"] = self.turn
        if self.turn == "next_round":
            self.round_manager()

        self.options = self.choose_random_word()
        self.draw_handler()
        # if guess is currect go to player and set the points

    async def start_turn():
        pass
    async def round_manager(self):
        await redis.incr(f"{self.room}:round")
        self.start_round()

    async def player_turn_manager(self):
        players = self.storage.get_players(self.room_name)
        for player in players:
            if await redis.get(f"{player}:played") == None:
                await redis.set(f"{player}:played", True)
                return player
        return "next_round"

    async def choose_random_word(self):
        options = random.sample(self.words, k=3)
        await redis.set(f"{self.room}:words")
        return options

    async def draw_handler(self):
        await redis.set(f"{self.turn}:drawing", True)
        
    async def init_jobs(self):
        await SendManager.update_players(self.room)
        await SendManager.set_round(self.room)

    async def init_player(player):
        pass