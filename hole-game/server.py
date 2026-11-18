"""Game server: a 2D object must reach a randomly placed hole.

The game runs in real time (TICK_RATE frames per second) and pushes every
frame to the player over a WebSocket. The player sends a direction at any
time; the server applies the latest direction on each tick.

Run:  uvicorn server:app --port 8000
"""
import asyncio
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

WIDTH, HEIGHT = 20, 20
TICK_RATE = 10  # frames per second
MAX_TICKS = 500  # end the game after this many ticks

DIRECTIONS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0), "stay": (0, 0)}

app = FastAPI()


def random_cell(exclude=None):
    while True:
        cell = [random.randrange(WIDTH), random.randrange(HEIGHT)]
        if cell != exclude:
            return cell


@app.websocket("/play")
async def play(ws: WebSocket):
    await ws.accept()

    obj = random_cell()
    hole = random_cell(exclude=obj)
    state = {"direction": "stay", "score": 0}

    async def receive_moves():
        # Runs alongside the game loop: just remembers the latest move.
        while True:
            msg = await ws.receive_json()
            if msg.get("action") in DIRECTIONS:
                state["direction"] = msg["action"]

    receiver = asyncio.create_task(receive_moves())
    try:
        for tick in range(MAX_TICKS):
            dx, dy = DIRECTIONS[state["direction"]]
            obj[0] = min(max(obj[0] + dx, 0), WIDTH - 1)
            obj[1] = min(max(obj[1] + dy, 0), HEIGHT - 1)

            event = None
            if obj == hole:
                state["score"] += 1
                hole = random_cell(exclude=obj)
                event = "scored"

            await ws.send_json({
                "type": "frame",
                "tick": tick,
                "obj": obj,
                "hole": hole,
                "width": WIDTH,
                "height": HEIGHT,
                "score": state["score"],
                "event": event,
            })
            await asyncio.sleep(1 / TICK_RATE)

        await ws.send_json({"type": "game_over", "score": state["score"]})
        await ws.close()
    except WebSocketDisconnect:
        pass
    finally:
        receiver.cancel()
