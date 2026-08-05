from services.redis_config import redis
import random

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

    async def start_game(self, room):
        self.room = room
        self.round = await redis.set(f"{room}:round", 1)
        self.round_number = int(await redis.get(f"{room}:round"))
        await self.start_round()

    async def start_round(self):
        if await redis.get(f"{self.room}:round") == 3:
            self.count_sccore()
            return

        self.turn = self.player_turn_manager()

        if self.turn == "next_round":
            self.round_manager()

        self.options = self.choose_random_word()
        self.draw_handler()
        # if guess is currect go to player and set the points

    async def round_manager(self):
        await redis.incr(f"{self.room}:round")
        self.start_round()

    async def player_turn_manager(self):
        self.players = await redis.smembers(self.room)
        for player in self.players:
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

    async def final_sccore(self):
        players = await redis.smembers(self.room)
        sccores = {}
        for player in players:
            sccore = await redis.get(f"{player}:sccore")
            sccores[player] = sccore
