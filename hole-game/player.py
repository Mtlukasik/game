"""Player: connects to the game, reacts to each frame, sends a direction.

Run (after the server is up):  python player.py
"""
import asyncio
import json

import websockets

URL = "ws://localhost:8000/play"


def choose_action(frame):
    """Simple greedy bot: move toward the hole, x first, then y."""
    (ox, oy), (hx, hy) = frame["obj"], frame["hole"]
    if ox < hx:
        return "right"
    if ox > hx:
        return "left"
    if oy < hy:
        return "down"
    if oy > hy:
        return "up"
    return "stay"


async def main():
    async with websockets.connect(URL) as ws:
        last_action = None
        async for raw in ws:
            msg = json.loads(raw)

            if msg["type"] == "game_over":
                print(f"Game over. Score: {msg['score']}")
                break

            if msg["event"] == "scored":
                print(f"tick {msg['tick']}: reached the hole! score={msg['score']}")

            action = choose_action(msg)
            if action != last_action:  # only send when the decision changes
                await ws.send(json.dumps({"action": action}))
                last_action = action


if __name__ == "__main__":
    asyncio.run(main())
