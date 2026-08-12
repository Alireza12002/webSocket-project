from app.game_manager.send_handler import SendHandler
from app.game_manager.storage import Storage
import random
import asyncio


class GameManager:
    words = ["Apple", "Bicycle", "Cactus", "Diamond", "Envelope",
             "Feather", "Guitar", "Helmet", "Igloo", "Jacket", "Map",
             "Alligator", "Bear", "Butterfly", "Cloud", "Dolphin",
             "Elephant", "Flower", "Giraffe", "Honeybee", "Island",
             "Banana", "Cake", "Door", "Egg", "Fork", "Glass", "Ring",
             "House", "Ice cream", "Kettle", "Anchor", "Bridge",
             "Castle", "Desert", "Elevator", "Forest", "Garden",
             "Harbor", "Ladder", "Mountain", "Balloon", "Camera",
             "Drum", "Kite", "Lamp",  "Pencil",  "Telescope", "Umbrella"
             ]

    def __init__(self):
        self.storage = Storage()
        self.send = SendHandler()
        self.timers = {}

    # Join and leave manager Functions

    async def join_handler(self, room, name):
        await self.update_players(room)
        await self.send.player_joined_chat(room, name)
        players = await self.storage.get_players(room)

        if len(players) == 4:
            asyncio.create_task(self.delayed_start(room))
            return
        for player in players.keys():
            await self.send.overlay_wait(player, "Wait until 4 player join!")

    async def handle_leave(self, room_name, name):
        await self.update_players(room_name)
        await self.send.player_leaved_chat(room_name, name)

    # Game state manager Functions
    async def delayed_start(self, room):
        await asyncio.sleep(0.5)
        await self.start_game(room)

    async def start_game(self, room_name):
        await self.update_players(room_name)
        await self.start_round(room_name)

    async def start_round(self, room_name):
        await self.storage.make_turn_order(room_name)
        room = await self.storage.get_room(room_name)
        room["round"] += 1
        if room["round"] > 2:
            winner_name = await self.choose_winner(room_name)
            await self.send.overlay_winner(room_name, winner_name)
            await asyncio.sleep(5)
            room["round"] = 0
            await self.storage.save_room(room_name, room)
            await self.start_game(room_name)
            return

        
        await self.send.set_round(room_name, room["round"])
        await self.storage.save_room(room_name, room)
        await self.start_turn(room_name)

    async def start_turn(self, room_name):
        drawer = await self.player_turn_manager(room_name)

        if drawer == "next_round":
            await self.start_round(room_name)
            return

        await self.clear_canvas(room_name, drawer)
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

    async def end_turn(self, room_name):
        await self.reveal_the_word(room_name)
        await asyncio.sleep(3)
        await self.score_board(room_name)
        await asyncio.sleep(3)
        
        await self.start_turn(room_name)

    # Game state manager helpers
    async def player_turn_manager(self, room_name):
        room = await self.storage.get_room(room_name)
        room["turn_index"] += 1

        if room["turn_index"] == 4:
            await self.storage.make_turn_order(room_name)
            return "next_round"

        turn = room["turn_order"][room["turn_index"]]
        await self.storage.save_room(room_name, room)
        return turn

    async def start_draw_handler(self, room_name):
        word = await self.storage.get_choosed_word(room_name)
        drawer = await self.storage.get_drawer(room_name)
        players = await self.storage.get_players(room_name)
        players = list(players.keys())

        if drawer in players:
            players.remove(drawer)
        drawer_name = await self.storage.get_name(room_name, drawer)
        # init jobs for drawer
        await self.send.player_drawing_chat(room_name, drawer_name)
        await self.send.overlay_off(drawer)
        await self.send.turn_on_toolbar(drawer)
        await self.send.choosed_word(drawer, word, "DRAW THIS")
        await self.start_timer(room_name)
        # for all
        await self.send.clear_chat(room_name)
        await self.update_players(room_name)
        # for gussers
        for player in players:
            await self.send.overlay_off(player)
            word = '_'*len(word)
            await self.send.choosed_word(player, word, "GUESS THIS")

    async def guess_handler(self, room_name, guess: str, name, channel_name):
        word: str = await self.storage.get_word(room_name)
        if guess.replace(" ", "").lower() == word.replace(" ", "").lower():
            await self.send.currect_guess(room_name, name)
            room = await self.storage.get_room(room_name)
            room["players"][channel_name]["guessed"] = True
            room["players"][channel_name]["score"] += 50
            drawer = room["drawer"]
            room["players"][drawer]["score"] += 50
            await self.storage.save_room(room_name, room)
            await self.check_all_guess(room_name)
            return
          
        await self.send.base_chat(room_name, name, guess)

    # Other helpers
    async def check_all_guess(self, room_name):
        players = await self.storage.get_players(room_name)
        await self.stop_timer(room_name)
        counter = 0
        for player in players.values():
            if player["guessed"] == True:
                counter += 1
        if counter == 3:
            await self.end_turn(room_name)

    async def update_players(self, room_name):
        room = await self.storage.get_room(room_name)
        players = room["players"]
        await self.send.send_players(room_name, players)

    async def clear_canvas(self, room_name, player):
        drawer = await self.storage.get_drawer(room_name)
        if player != drawer:
            return

        await self.send.clear_canvas(room_name)

    async def score_board(self, room_name):
        players_data = []
        players = await self.storage.get_players(room_name)

        for player in players.values():
            players_data.append({
                "name": player["name"],
                "score": player["score"]
            })

        await self.send.score_board(room_name, players_data)

    async def start_timer(self, room_name):
        seconds = 5

        async def countdown():
            try:
                for time in range(seconds, -1, -1):
                    await self.send.round_timer(room_name, time)

                    if time == 0:
                        await self.end_turn(room_name)
                        print("endturn")
                        return

                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                pass

        self.timers[room_name] = asyncio.create_task(countdown())

    async def stop_timer(self, room_name):
        timer = self.timers.get(room_name)
        if timer:
            timer.cancel()

    async def choose_random_word(self):
        options = random.sample(self.words, k=3)
        return options

    async def reveal_the_word(self, room_name):
        word = await self.storage.get_word(room_name)
        await self.send.overlay_reveal(room_name, word)

    async def choose_winner(self, room_name):
        players = await self.storage.get_players(room_name)
        players = players.values()
        score = 0

        for player in players:
            if player["score"] > score:
                score = player["score"]
                winner = player["name"]

        return winner

        