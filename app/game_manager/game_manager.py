from app.game_manager.send_handler import SendHandler
from app.game_manager.storage import Storage
from services.redis_config import redis
import random
import json
import asyncio
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
        self.word_event = asyncio.Event()
        self.storage = Storage()
        self.send = SendHandler()

    async def join_handler(self, room):
        await self.update_players(room)
        print(f"{room} game started players{await self.storage.get_players(room)}")
        if len(await self.storage.get_players(room)) == 4:
            await self.start_game(room)

    async def start_game(self, room_name):
        await self.update_players(room_name)
        self.room_name = room_name
        #await self.init_jobs()
        await self.start_round()

    async def start_round(self):
        room = await self.storage.get_room(self.room_name)
        if room["round"] == 4:
            return # show sccores
        room["round"] += 1
        await self.send.set_round(self.room_name, room["round"])
        await self.storage.save_room(self.room_name, room)
        await self.start_turn()
        # if guess is currect go to player and set the points

    async def start_turn(self):
        self.drawer = await self.player_turn_manager() #make a new turn system
        room = await self.storage.get_room(self.room_name)
        if self.drawer == "next_round":
            await self.start_round()
        room["drawer"] = self.drawer

        await self.storage.save_room(self.room_name, room)
        words = await self.choose_random_word()
        await self.send.send_words(self.drawer, words)
        
        await self.word_event.wait()
        self.word_event.clear()
        # findall of the jobs to start a drawing and then start it 
        await self.start_draw_handler()

    async def player_turn_manager(self):
        await self.storage.make_turn_order(self.room_name)
        room = await self.storage.get_room(self.room_name)
        room["turn_index"] += 1
        turn = room["turn_order"][room["turn_index"]]
        if room["turn_index"] == 4:
            await self.storage.make_turn_order(self.room_name)
            return "next_round"
        await self.storage.save_room(self.room_name, room)
        return turn

    async def choose_random_word(self):
        options = random.sample(self.words, k=3)
        return options

    async def start_draw_handler(self):
        word = await self.storage.get_choosed_word(self.room_name)
        players = await self.storage.get_players(self.room_name)
        players = list(players.keys())
        players.remove(self.drawer)
        for player in players:
            await self.send.overlay_wait(player, "Wait for drawer to choose...")
        # init jobs for drawer
        await self.send.overlay_off(self.drawer)
        await self.send.turn_on_toolbar(self.drawer)
        await self.send.choosed_word(self.drawer, word, "DRAW THIS")
        # for all
        await self.send.clear_chat(self.room_name)
        # for gussers
        for player in players:
            await self.send.overlay_off(player)
            word = '_'*len(word)
            await self.send.choosed_word(player, word, "GUESS THIS")

    async def guess_handler(self, room_name, guess, name):
        word = await self.storage.get_word(room_name)
        if guess == word:
            await self.send.currect_guess(room_name, name)
            #true guessed
        await self.send.base_chat(room_name, name, guess)
        await self.check_all_guess()

    async def check_all_guess(self):
        players = await self.storage.get_players(self.room_name)
        counter = 0
        for player in players.values():
            if player["guessed"] == True:
                counter += 1
        if counter == 3:
            await self.end_turn()

    async def end_turn(self):
        await self.start_turn()

    async def receive_choice(self):
        self.word_event.set()

    async def init_jobs(self):
        pass

    async def update_players(self, room_name):
        room = await self.storage.get_room(room_name)
        players = room["players"]  # Keep as dict with channel_name keys
        await self.send.send_players(room_name, players)

    async def handle_leave(self, room_name):
        await self.update_players(room_name)


