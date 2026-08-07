from app.game_manager.send_handler import SendHandler, SendManager
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
        self.storage = Storage()
        self.send = SendHandler()

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
        self.storage.save_room(self.room_name, room)
        self.start_turn()
        # if guess is currect go to player and set the points

    async def start_turn(self):
        words = self.choose_random_word()
        self.send.send_words(self.turn, words)
        # findall of the jobs to start a drawing and then start it 
        self.draw_handler()
        self.handle_guess()

    async def player_turn_manager(self):
        await self.storage.make_turn_order(self.room_name)
        room = await self.storage.get_room(self.room_name)
        room["turn_index"] += 1
        turn = room["turn_order"][room["turn_index"]]
        await self.storage.save_room(self.room_name, room)
        if room["turn_index"] == 4:
            self.storage.make_turn_order(self.room_name)
            return "next_round"
        return turn

    async def choose_random_word(self):
        options = random.sample(self.words, k=3)
        await redis.set(f"{self.room}:words")
        return options

    async def draw_handler(self):
        pass
        
    async def init_jobs(self):
        await SendManager.update_players(self.room)
        await SendManager.set_round(self.room)
