from app.game_manager.send_handler import SendHandler
from app.game_manager.storage import Storage
import random
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
        self.storage = Storage()
        self.send = SendHandler()

    async def join_handler(self, room):
        await self.update_players(room)
        players = await self.storage.get_players(room)

        if len(players) == 4:
            asyncio.create_task(self.delayed_start(room))
            # await self.start_game(room)

    async def delayed_start(self, room):
        await asyncio.sleep(0.5)
        await self.start_game(room)


    async def start_game(self, room_name):
        await self.update_players(room_name)
        await self.start_round(room_name)

    async def start_round(self, room_name):
        await self.storage.make_turn_order(room_name)
        room = await self.storage.get_room(room_name)
        if room["round"] == 4:
            return # show sccores
        room["round"] += 1
        await self.send.set_round(room_name, room["round"])
        await self.storage.save_room(room_name, room)
        await self.start_turn(room_name)
        # if guess is currect go to player and set the points

    async def start_turn(self, room_name):
        await self.clear_canvas(room_name)
        drawer = await self.player_turn_manager(room_name) 

        if drawer == "next_round":
            await self.start_round(room_name)
            return
        
        players = await self.storage.get_players(room_name)
        room = await self.storage.get_room(room_name)   
        for player in players:
            room["players"][player]["drawing"] = False
            room["players"][player]["guessed"] = False

     
        room["drawer"] = drawer
        room["players"][drawer]["drawing"] = True


        await self.storage.save_room(room_name, room)
        await self.update_players(room_name)
        words = await self.choose_random_word()
        await self.send.send_words(drawer, words)

        
        for player in players:
            if player != drawer:
                await self.send.overlay_wait(player, "Wait for drawer to choose...")
      
    async def player_turn_manager(self, room_name):
        # await self.storage.make_turn_order(room_name)
        room = await self.storage.get_room(room_name)
        room["turn_index"] += 1

        if room["turn_index"] == 4:
            await self.storage.make_turn_order(room_name)
            return "next_round"

        turn = room["turn_order"][room["turn_index"]]        
        await self.storage.save_room(room_name, room)
        return turn

    async def choose_random_word(self):
        options = random.sample(self.words, k=3)
        return options

    async def start_draw_handler(self, room_name):
        word = await self.storage.get_choosed_word(room_name)
        drawer = await self.storage.get_drawer(room_name)
        players = await self.storage.get_players(room_name)
        players = list(players.keys())

        if drawer in players:
            players.remove(drawer)

        # init jobs for drawer
        await self.send.overlay_off(drawer)
        await self.send.turn_on_toolbar(drawer)
        await self.send.choosed_word(drawer, word, "DRAW THIS")
        # for all
        await self.send.clear_chat(room_name)
        await self.update_players(room_name)
        # for gussers
        for player in players:
            await self.send.overlay_off(player)
            word = '_'*len(word)
            await self.send.choosed_word(player, word, "GUESS THIS")

    async def guess_handler(self, room_name, guess, name, channel_name):
        word = await self.storage.get_word(room_name)
        if guess == word:
            await self.send.currect_guess(room_name, name)
            room = await self.storage.get_room(room_name)
            room["players"][channel_name]["guessed"] = True
            await self.storage.save_room(room_name, room)
            await self.check_all_guess(room_name)
            return
            #true guessed
        await self.send.base_chat(room_name, name, guess)
        

    async def check_all_guess(self, room_name):
        players = await self.storage.get_players(room_name)
        counter = 0
        for player in players.values():
            if player["guessed"] == True:
                counter += 1
        if counter == 3:
            await self.start_turn(room_name)

    async def update_players(self, room_name):
        room = await self.storage.get_room(room_name)
        players = room["players"]  # Keep as dict with channel_name keys
        await self.send.send_players(room_name, players)

    async def handle_leave(self, room_name):
        await self.update_players(room_name)

    async def clear_canvas(self, room_name):
        await self.send.clear_canvas(room_name)