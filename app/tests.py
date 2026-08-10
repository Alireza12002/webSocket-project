import asyncio
import json
from unittest.mock import AsyncMock

from django.test import SimpleTestCase

from app.consumers import GameConsumer
from app.game_manager.send_handler import SendHandler


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


class SendPlayersMeFlagTest(SimpleTestCase):
    """The drawer's client decides it may draw by finding the player entry
    flagged with "me": True and reading its "drawing" value. If that flag is
    missing, every client disables drawing and the drawer cannot draw."""

    def _send(self, players):
        handler = SendHandler()
        handler.channel_layer = AsyncMock()
        asyncio.run(handler.send_players("room1", players))
        return {
            call.args[0]: call.args[1]["players"]
            for call in handler.channel_layer.send.await_args_list
        }

    def test_each_recipient_is_flagged_as_me_exactly_once(self):
        players = {
            "chan.a": {"name": "Alice", "drawing": True},
            "chan.b": {"name": "Bob", "drawing": False},
            "chan.c": {"name": "Cara", "drawing": False},
        }

        per_recipient = self._send(players)

        self.assertEqual(set(per_recipient), set(players))

        for channel, players_list in per_recipient.items():
            flagged = [p for p in players_list if p.get("me")]
            self.assertEqual(len(flagged), 1, f"{channel} needs exactly one 'me'")
            self.assertEqual(flagged[0]["name"], players[channel]["name"])
            self.assertEqual(len(players_list), len(players))

    def test_drawer_receives_me_entry_with_drawing_true(self):
        players = {
            "chan.a": {"name": "Alice", "drawing": True},
            "chan.b": {"name": "Bob", "drawing": False},
        }

        per_recipient = self._send(players)

        drawer_view = next(p for p in per_recipient["chan.a"] if p["me"])
        self.assertTrue(drawer_view["drawing"], "drawer must be able to draw")

        guesser_view = next(p for p in per_recipient["chan.b"] if p["me"])
        self.assertFalse(guesser_view["drawing"], "guesser must not draw")

    def test_original_player_state_is_not_mutated(self):
        players = {"chan.a": {"name": "Alice", "drawing": True}}

        self._send(players)

        self.assertNotIn("me", players["chan.a"])

