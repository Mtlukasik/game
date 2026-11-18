# Hole game over WebSocket

Two apps:
- `server.py` hosts the game. It runs at 10 frames/sec and pushes every frame to the player.
- `player.py` plays the game. It reads each frame and sends a direction back.

## Run

```bash
cd hole-game
pip install -r requirements.txt

# terminal 1
uvicorn server:app --port 8000

# terminal 2
python player.py
```

## Protocol

Server → player, every tick:
```json
{"type": "frame", "tick": 42, "obj": [3, 7], "hole": [12, 5],
 "width": 20, "height": 20, "score": 1, "event": null}
```
`event` is `"scored"` on the tick the object reaches the hole. Then a new hole appears.
After 500 ticks the server sends `{"type": "game_over", "score": N}`.

Player → server, whenever it wants:
```json
{"action": "up" | "down" | "left" | "right" | "stay"}
```
The object keeps moving in the last direction it received.

To build a smarter player, replace `choose_action()` in `player.py`.
