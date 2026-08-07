import random

from services.redis_config import redis
import json


class Storage:
    PLAYER_COLORS = [
        "#4571FF",  # Blue
        "#FF4D4D",  # Red
        "#2ECC71",  # Green
        "#F1C40F",  # Yellow
        "#9B59B6",  # Purple
        "#E67E22",  # Orange
        "#1ABC9C",  # Turquoise
        "#E91E63",  # Pink
        "#795548",  # Brown
        "#607D8B",  # Blue Grey
        "#3F51B5",  # Indigo
        "#00BCD4",  # Cyan
        "#8BC34A",  # Light Green
        "#CDDC39",  # Lime
        "#FFC107",  # Amber
        "#FF9800",  # Deep Orange
        "#673AB7",  # Deep Purple
        "#009688",  # Teal
        "#2196F3",  # Sky Blue
        "#4CAF50",  # Emerald
        "#C2185B",  # Raspberry
        "#D81B60",  # Magenta
        "#7CB342",  # Olive Green
        "#5C6BC0",  # Soft Indigo
        "#26A69A",  # Aqua
        "#42A5F5",  # Bright Blue
        "#AB47BC",  # Violet
        "#EC407A",  # Rose
        "#FFA726",  # Golden Orange
        "#66BB6A",  # Fresh Green
        "#29B6F6",  # Ocean Blue
        "#EF5350",  # Coral Red
        "#8D6E63",  # Coffee
        "#78909C",  # Steel
        "#C0CA33",  # Lime Green
        "#F06292",  # Hot Pink
        "#7E57C2",  # Lavender
        "#26C6DA",  # Bright Cyan
        "#FF7043",  # Salmon
        "#9CCC65",  # Apple Green
    ]

    async def init_room(room_name):
        room = {
            "name": room_name,
            "round": 0,
            "drawer": None,
            "clock": None,
            "word": None,
            "players": {}
        }
        await redis.set(f"room:{room_name}", json.dumps(room))

    async def get_rooms():
        return await redis.get("rooms")

    async def add_room(room_name):
        await redis.set("rooms", room_name)

    async def add_player_to_the_room(self, channel_name, room_name, name):
        availabe = self.PLAYER_COLORS.copy()
        color = random.choice(availabe)
        availabe.remove(color)
        room = json.loads(await redis.get(f"room:{room_name}"))
        room["players"][channel_name] = {
            "name": name,
            "score": 0,
            "drawing": False,
            "guessed": False,
            "color":color
        }

    async def get_players(room_name):
        data = await redis.get(f"room:{room_name}")
        if data is None:
            return {}
        room = json.loads(data)
        return room["players"]

    async def get_room(self, room_name):
        room = json.loads(await redis.get(f"room:{room_name}"))
        return room
    async def save_room(self, room_name, data):
        await redis.set(f"room:{room_name}", json.dumps(data))
        