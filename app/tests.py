import asyncio
import json
from unittest.mock import AsyncMock

from django.test import SimpleTestCase

from app.consumers import GameConsumer


class GameConsumerPlayerMessageShapeTest(SimpleTestCase):
    def test_send_players_uses_ui_players_shape(self):
        consumer = GameConsumer()
        consumer.send = AsyncMock()

        event = {
            "players": [
                {"name": "Alice", "score": 0, "guessed": False, "drawing": False, "color": "#4571FF"}
            ]
        }

        asyncio.run(consumer.send_players(event))

        sent_json = consumer.send.await_args.args[0]
        payload = json.loads(sent_json)

        self.assertEqual(payload["type"], "ui")
        self.assertEqual(payload["action"], "players")
        self.assertIn("players", payload)
        self.assertNotIn("payload", payload)
        self.assertEqual(payload["players"], event["players"])
