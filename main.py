import pygame
import sys
import random
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

# ── CONSTANTS & ENUMS ─────────────────────────────────────────────────────────
GRID_SIZE  = 10
CELL_SIZE  = 60
GX         = 25                                    # grid origin x
GY         = 25                                    # grid origin y
PANEL_X    = GX + GRID_SIZE * CELL_SIZE + 18      # = 643
PANEL_W    = 290
WIN_W      = PANEL_X + PANEL_W + 7                # ≈ 940
WIN_H      = GY + GRID_SIZE * CELL_SIZE + 25      # = 650

# Colors
BLK  = (  0,  0,  0); WHT  = (230,230,240); GRY  = (120,120,130)
DGRY = ( 45, 45, 58); RED  = (220, 55, 55); GRN  = ( 55,200, 75)
BLU  = ( 60,120,230); PRP  = (160, 60,230); ORG  = (225,135, 50)
YLW  = (225,205, 55); CYN  = ( 55,205,205); PNK  = (225,105,155)
DRED = (110, 18, 18); DGRN = ( 18, 95, 18); DBLU = ( 18, 48,145)
DPRP = ( 70, 18,128); GDBG = ( 28, 28, 42); CBG  = ( 40, 40, 56)
PBG  = ( 20, 20, 32); SEP  = ( 58, 58, 75)

class Phase(Enum):
    PLAYER = "player"
    BOTS   = "bots"
    WIN    = "win"
    LOSE   = "lose"

class Mode(Enum):
    NONE     = "none"
    MOVE     = "move"
    STRIKE   = "strike"
    SHOOT    = "shoot"
    FIREBALL = "fireball"

class BC(Enum):
    WARRIOR = "Warrior"
    ARCHER  = "Archer"
    MAGE    = "Mage"
    ROGUE   = "Rogue"

# ── STATS ─────────────────────────────────────────────────────────────────────
@dataclass
class Stats:
    strength:  int   # melee damage bonus
    agility:   int   # dodge / ranged bonus
    speed:     int   # cells per move step
    condition: int   # max HP

    def copy(self) -> "Stats":
        return Stats(self.strength, self.agility, self.speed, self.condition)

PLAYER_STATS = Stats(6, 5, 3, 100)

BOT_STATS = {
    BC.WARRIOR: Stats(8, 3, 2, 85),
    BC.ARCHER:  Stats(3, 8, 3, 55),
    BC.MAGE:    Stats(4, 4, 2, 50),
    BC.ROGUE:   Stats(5, 6, 5, 60),
}

BOT_CLR = {
    BC.WARRIOR: (RED,  DRED),
    BC.ARCHER:  (GRN,  DGRN),
    BC.MAGE:    (PRP,  DPRP),
    BC.ROGUE:   (ORG,  (128, 68, 18)),
}

BOT_START = {
    BC.WARRIOR: (9, 9),
    BC.ARCHER:  (9, 0),
    BC.MAGE:    (5, 8),
    BC.ROGUE:   (0, 9),
}

# ── ENTITIES ──────────────────────────────────────────────────────────────────
class Character:
    def __init__(self, name: str, stats: Stats, x: int, y: int):
        self.name   = name
        self.stats  = stats
        self.x, self.y = x, y
        self.hp     = stats.condition
        self.ap     = 0

    @property
    def max_ap(self) -> int:
        return self.stats.speed + 2

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def start_turn(self):
        self.ap = self.max_ap

    def damage(self, d: int):
        self.hp = max(0, self.hp - d)

    def heal_hp(self, a: int):
        self.hp = min(self.stats.condition, self.hp + a)


class Player(Character):
    def __init__(self, x: int, y: int):
        super().__init__("Player", PLAYER_STATS.copy(), x, y)
        self.charges = {"fireball": 3, "heal": 3}


class Bot(Character):
    def __init__(self, bc: BC, idx: int):
        sx, sy = BOT_START[bc]
        super().__init__(f"{bc.value} {idx}", BOT_STATS[bc].copy(), sx, sy)
        self.bc  = bc
        self.clr = BOT_CLR[bc]


# ── GRID ──────────────────────────────────────────────────────────────────────
class Grid:
    def __init__(self):
        self._c: List[List[Optional[Character]]] = \
            [[None] * GRID_SIZE for _ in range(GRID_SIZE)]

    def ok(self, x: int, y: int) -> bool:
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def get(self, x: int, y: int) -> Optional[Character]:
        return self._c[y][x] if self.ok(x, y) else None

    def place(self, c: Character):
        self._c[c.y][c.x] = c

    def remove(self, c: Character):
        if self.ok(c.x, c.y) and self._c[c.y][c.x] is c:
            self._c[c.y][c.x] = None

    def move(self, c: Character, nx: int, ny: int) -> bool:
        if not self.ok(nx, ny) or self._c[ny][nx]:
            return False
        self.remove(c)
        c.x, c.y = nx, ny
        self.place(c)
        return True

    def adj(self, x: int, y: int) -> List[Tuple[int, int]]:
        return [(x+dx, y+dy) for dx, dy in ((0,1),(0,-1),(1,0),(-1,0))
                if self.ok(x+dx, y+dy)]


# ── COMBAT ────────────────────────────────────────────────────────────────────
def roll(sides: int) -> int:
    return random.randint(1, sides)


def melee_dmg(attacker: Character, defender: Character) -> Tuple[int, bool]:
    """Returns (damage, dodged)."""
    if roll(20) <= defender.stats.agility:
        return 0, True
    dmg = roll(6) + attacker.stats.strength
    return dmg, False


def ranged_dmg(attacker: Character, dist: int) -> Tuple[int, bool]:
    """Returns (damage, hit)."""
    hit_chance = max(0.25, 1.0 - dist * 0.07)
    if random.random() > hit_chance:
        return 0, False
    dmg = roll(4) + attacker.stats.agility // 2
    return dmg, True


def fireball_dmg(attacker: Character) -> int:
    return roll(8) + attacker.stats.strength // 2


def heal_amount(caster: Character) -> int:
    return roll(10) + caster.stats.strength * 2


# ── LOG ───────────────────────────────────────────────────────────────────────
class Log:
    def __init__(self, cap: int = 50):
        self._cap = cap
        self.lines: List[Tuple[str, tuple]] = []

    def add(self, msg: str, color: tuple = WHT):
        self.lines.append((msg[:38], color))
        if len(self.lines) > self._cap:
            self.lines.pop(0)


# ── GAME ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.grid   = Grid()
        self.log    = Log()
        self.phase  = Phase.PLAYER
        self.mode   = Mode.NONE
        self.turn   = 0
        self.hover  = None          # (gx, gy) mouse hover cell
        self._setup()

    def _setup(self):
        self.player = Player(0, 0)
        self.grid.place(self.player)
        self.bots: List[Bot] = []
        for i, bc in enumerate([BC.WARRIOR, BC.ARCHER, BC.MAGE, BC.ROGUE]):
            b = Bot(bc, i + 1)
            self.bots.append(b)
            self.grid.place(b)
        self.player.start_turn()
        self.log.add("Your turn! Choose an action.", CYN)

    @property
    def alive_bots(self) -> List[Bot]:
        return [b for b in self.bots if b.alive]

    # ── player actions ────────────────────────────────────────────────────────
    def player_move(self, nx: int, ny: int) -> bool:
        cost = abs(nx - self.player.x) + abs(ny - self.player.y)
        if cost < 1 or cost > self.player.ap:
            self.log.add("Can't reach — not enough AP.", GRY)
            return False
        if self.grid.move(self.player, nx, ny):
            self.player.ap -= cost
            self.log.add(f"Move → ({nx},{ny})  AP left: {self.player.ap}", WHT)
            return True
        self.log.add("Cell is blocked.", GRY)
        return False

    def player_strike(self, tx: int, ty: int) -> bool:
        if self.player.ap < 2:
            self.log.add("Strike needs 2 AP.", GRY); return False
        dist = abs(tx - self.player.x) + abs(ty - self.player.y)
        if dist != 1:
            self.log.add("Strike: adjacent cells only.", GRY); return False
        t = self.grid.get(tx, ty)
        if not isinstance(t, Bot):
            self.log.add("No enemy there.", GRY); return False
        dmg, dodged = melee_dmg(self.player, t)
        self.player.ap -= 2
        if dodged:
            self.log.add(f"{t.name} dodged your strike!", GRY)
        else:
            t.damage(dmg)
            self.log.add(f"Strike! {t.name} −{dmg} HP", YLW)
            self._kill(t)
        return True

    def player_shoot(self, tx: int, ty: int) -> bool:
        if self.player.ap < 2:
            self.log.add("Shoot needs 2 AP.", GRY); return False
        t = self.grid.get(tx, ty)
        if not isinstance(t, Bot):
            self.log.add("No enemy there.", GRY); return False
        dist = abs(tx - self.player.x) + abs(ty - self.player.y)
        dmg, hit = ranged_dmg(self.player, dist)
        self.player.ap -= 2
        if hit:
            t.damage(dmg)
            self.log.add(f"Shot! {t.name} −{dmg} HP  (dist {dist})", YLW)
            self._kill(t)
        else:
            self.log.add(f"Shot missed {t.name}! (dist {dist})", GRY)
        return True

    def player_fireball(self, tx: int, ty: int) -> bool:
        if self.player.charges["fireball"] <= 0:
            self.log.add("No Fireball charges left!", GRY); return False
        if self.player.ap < 3:
            self.log.add("Fireball needs 3 AP.", GRY); return False
        self.player.charges["fireball"] -= 1
        self.player.ap -= 3
        hits = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                t = self.grid.get(tx + dx, ty + dy)
                if isinstance(t, Bot):
                    dmg = fireball_dmg(self.player)
                    t.damage(dmg)
                    hits += 1
                    self._kill(t)
        self.log.add(f"Fireball at ({tx},{ty})! {hits} hit.", ORG)
        return True

    def player_heal(self) -> bool:
        if self.player.charges["heal"] <= 0:
            self.log.add("No Heal charges left!", GRY); return False
        if self.player.ap < 2:
            self.log.add("Heal needs 2 AP.", GRY); return False
        amt = heal_amount(self.player)
        self.player.heal_hp(amt)
        self.player.charges["heal"] -= 1
        self.player.ap -= 2
        self.log.add(
            f"Healed +{amt} HP  ({self.player.hp}/{self.player.stats.condition})", GRN)
        return True

    def end_player_turn(self):
        self.mode = Mode.NONE
        self.phase = Phase.BOTS
        self.log.add("─── Bot turns ───", GRY)

    def _kill(self, b: Bot):
        if not b.alive:
            self.grid.remove(b)
            self.log.add(f"{b.name} defeated!", RED)
            if not self.alive_bots:
                self.phase = Phase.WIN
                self.log.add("All enemies defeated! VICTORY!", GRN)

    # ── bot AI ────────────────────────────────────────────────────────────────
    def run_bots(self):
        for b in self.alive_bots:
            b.start_turn()
            self._bot_act(b)
        self.turn += 1
        if self.player.alive:
            self.phase = Phase.PLAYER
            self.player.start_turn()
            self.log.add(f"─── Turn {self.turn + 1}: Your turn ───", CYN)
        else:
            self.phase = Phase.LOSE
            self.log.add("You were defeated! GAME OVER.", RED)

    def _toward(self, b: Bot, steps: int):
        for _ in range(steps):
            if b.ap <= 0:
                break
            px, py = self.player.x, self.player.y
            dx, dy = px - b.x, py - b.y
            opts = []
            if dx:
                opts.append((b.x + (1 if dx > 0 else -1), b.y))
            if dy:
                opts.append((b.x, b.y + (1 if dy > 0 else -1)))
            random.shuffle(opts)
            moved = False
            for nx, ny in opts:
                if self.grid.move(b, nx, ny):
                    b.ap -= 1
                    moved = True
                    break
            if not moved:
                break

    def _away(self, b: Bot, steps: int):
        for _ in range(steps):
            if b.ap <= 0:
                break
            px, py = self.player.x, self.player.y
            dx, dy = b.x - px, b.y - py
            opts = []
            if dx:
                opts.append((b.x + (1 if dx > 0 else -1), b.y))
            if dy:
                opts.append((b.x, b.y + (1 if dy > 0 else -1)))
            random.shuffle(opts)
            moved = False
            for nx, ny in opts:
                if self.grid.move(b, nx, ny):
                    b.ap -= 1
                    moved = True
                    break
            if not moved:
                break

    def _bot_act(self, b: Bot):
        p = self.player
        dist = lambda: abs(b.x - p.x) + abs(b.y - p.y)

        if b.bc == BC.WARRIOR:
            self._toward(b, b.stats.speed)
            if dist() == 1 and b.ap >= 2:
                dmg, dodged = melee_dmg(b, p)
                b.ap -= 2
                if dodged:
                    self.log.add(f"{b.name} missed (dodged)!", GRY)
                else:
                    p.damage(dmg)
                    self.log.add(f"{b.name} strikes for {dmg}!", RED)

        elif b.bc == BC.ARCHER:
            if dist() <= 2:
                self._away(b, 2)
            d = dist()
            if d <= 7 and b.ap >= 2:
                dmg, hit = ranged_dmg(b, d)
                b.ap -= 2
                if hit:
                    p.damage(dmg)
                    self.log.add(f"{b.name} shoots for {dmg}!", RED)
                else:
                    self.log.add(f"{b.name} shot missed!", GRY)
            elif d > 7:
                self._toward(b, 2)

        elif b.bc == BC.MAGE:
            d = dist()
            if 3 <= d <= 6 and b.ap >= 3:
                dmg = fireball_dmg(b)
                p.damage(dmg)
                b.ap -= 3
                self.log.add(f"{b.name} casts Fireball for {dmg}!", PRP)
            elif d < 3:
                self._away(b, 2)
            else:
                self._toward(b, 2)

        elif b.bc == BC.ROGUE:
            self._toward(b, b.stats.speed)
            while dist() == 1 and b.ap >= 2:
                dmg, dodged = melee_dmg(b, p)
                b.ap -= 2
                if dodged:
                    self.log.add(f"{b.name} missed (dodged)!", GRY)
                    break
                else:
                    p.damage(dmg)
                    self.log.add(f"{b.name} backstabs for {dmg}!", PNK)


# ── RENDERER ──────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.fsm = pygame.font.SysFont("monospace", 13)
        self.fmd = pygame.font.SysFont("monospace", 16)
        self.flg = pygame.font.SysFont("monospace", 21, bold=True)
        self.fxl = pygame.font.SysFont("monospace", 42, bold=True)
        # Buttons (positions set once; updated dynamically in draw)
        self._btns: List[dict] = []
        self._build_buttons()

    def _build_buttons(self):
        bx = PANEL_X
        # y will be updated each frame before drawing
        self._btns = [
            {"lbl": "Move  [M]",      "mode": Mode.MOVE,     "clr": BLU,  "row": 0, "col": 0},
            {"lbl": "Strike[S]",      "mode": Mode.STRIKE,   "clr": YLW,  "row": 0, "col": 1},
            {"lbl": "Shoot [R]",      "mode": Mode.SHOOT,    "clr": GRN,  "row": 1, "col": 0},
            {"lbl": "Firebll[F]",     "mode": Mode.FIREBALL, "clr": ORG,  "row": 1, "col": 1},
            {"lbl": "Heal  [H]",      "mode": None,          "clr": PNK,  "row": 2, "col": 0},
            {"lbl": "End Turn[E]",    "mode": None,          "clr": GRY,  "row": 2, "col": 1},
        ]
        for btn in self._btns:
            btn["rect"] = pygame.Rect(0, 0, 130, 30)   # x/y filled each frame

    def button_rects(self) -> List[dict]:
        return self._btns

    def draw(self, game: Game):
        self.screen.fill(GDBG)
        self._grid(game)
        btn_top = self._panel(game)
        self._update_btn_rects(btn_top)
        self._buttons(game)
        if game.phase == Phase.WIN:
            self._overlay("VICTORY!", GRN)
        elif game.phase == Phase.LOSE:
            self._overlay("GAME OVER", RED)

    def _update_btn_rects(self, top_y: int):
        bx = PANEL_X
        bw, bh, gap = 130, 30, 8
        for btn in self._btns:
            col_off = btn["col"] * (bw + gap)
            row_off = btn["row"] * (bh + gap)
            btn["rect"] = pygame.Rect(bx + col_off, top_y + row_off, bw, bh)

    # ── grid ──────────────────────────────────────────────────────────────────
    def _grid(self, game: Game):
        g = game
        p = g.player

        # Reachable / targetable highlights
        hi_move: set  = set()
        hi_enemy: set = set()
        hi_aoe: set   = set()

        if g.phase == Phase.PLAYER:
            m = g.mode
            if m == Mode.MOVE:
                for cx in range(GRID_SIZE):
                    for cy in range(GRID_SIZE):
                        cost = abs(cx - p.x) + abs(cy - p.y)
                        if 0 < cost <= p.ap and not g.grid.get(cx, cy):
                            hi_move.add((cx, cy))
            elif m == Mode.STRIKE:
                for nx, ny in g.grid.adj(p.x, p.y):
                    if isinstance(g.grid.get(nx, ny), Bot):
                        hi_enemy.add((nx, ny))
            elif m == Mode.SHOOT:
                for b in g.alive_bots:
                    hi_enemy.add((b.x, b.y))
            elif m == Mode.FIREBALL:
                for b in g.alive_bots:
                    hi_enemy.add((b.x, b.y))
                if g.hover:
                    hx, hy = g.hover
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            if g.grid.ok(hx + dx, hy + dy):
                                hi_aoe.add((hx + dx, hy + dy))

        # Draw cells
        for cy in range(GRID_SIZE):
            for cx in range(GRID_SIZE):
                rx = GX + cx * CELL_SIZE
                ry = GY + cy * CELL_SIZE
                if (cx, cy) in hi_aoe:
                    bg = (90, 60, 20)
                elif (cx, cy) in hi_move:
                    bg = (35, 70, 45)
                elif (cx, cy) in hi_enemy:
                    bg = (80, 30, 30)
                else:
                    bg = CBG
                pygame.draw.rect(self.screen, bg, (rx, ry, CELL_SIZE - 1, CELL_SIZE - 1))
                c = g.grid.get(cx, cy)
                if c and c.alive:
                    self._char(c, rx, ry)

        # Grid lines
        for i in range(GRID_SIZE + 1):
            ex = GX + i * CELL_SIZE
            ey = GY + i * CELL_SIZE
            pygame.draw.line(self.screen, DGRY, (ex, GY), (ex, GY + GRID_SIZE * CELL_SIZE))
            pygame.draw.line(self.screen, DGRY, (GX, ey), (GX + GRID_SIZE * CELL_SIZE, ey))

        # Coordinate labels
        for i in range(GRID_SIZE):
            lbl = self.fsm.render(str(i), True, (70, 70, 85))
            self.screen.blit(lbl, (GX + i * CELL_SIZE + CELL_SIZE // 2 - 4, GY - 16))
            self.screen.blit(lbl, (GX - 14, GY + i * CELL_SIZE + CELL_SIZE // 2 - 7))

    def _char(self, c: Character, rx: int, ry: int):
        if isinstance(c, Player):
            fg, bg = BLU, DBLU
        else:
            fg, bg = c.clr
        pad = 6
        inner = pygame.Rect(rx + pad, ry + pad, CELL_SIZE - 1 - 2 * pad, CELL_SIZE - 1 - 2 * pad)
        pygame.draw.rect(self.screen, bg, inner)
        pygame.draw.rect(self.screen, fg, inner, 2)
        lbl = self.fmd.render(c.name[0], True, WHT)
        self.screen.blit(lbl, (rx + CELL_SIZE // 2 - lbl.get_width() // 2,
                                ry + CELL_SIZE // 2 - lbl.get_height() // 2))
        # HP bar
        bw = CELL_SIZE - 10
        hp_r = c.hp / c.stats.condition
        pygame.draw.rect(self.screen, DRED, (rx + 5, ry + CELL_SIZE - 10, bw, 5))
        hc = GRN if hp_r > 0.5 else (YLW if hp_r > 0.25 else RED)
        pygame.draw.rect(self.screen, hc, (rx + 5, ry + CELL_SIZE - 10, int(bw * hp_r), 5))
        # AP pips (player only)
        if isinstance(c, Player):
            for i in range(c.max_ap):
                clr = CYN if i < c.ap else DGRY
                pygame.draw.circle(self.screen, clr,
                                   (rx + 7 + i * 10, ry + CELL_SIZE - 17), 3)

    # ── panel ─────────────────────────────────────────────────────────────────
    def _panel(self, game: Game) -> int:
        """Draw panel, return y where action buttons should start."""
        g = game
        pygame.draw.rect(self.screen, PBG, (PANEL_X - 5, 0, PANEL_W + 10, WIN_H))
        x = PANEL_X
        y = 10

        # Title
        self._t("GRID GAME", x, y, self.flg, CYN); y += 32

        # Phase / turn
        if g.phase == Phase.PLAYER:
            ps, pc = f"Turn {g.turn + 1}  YOUR TURN", GRN
        elif g.phase == Phase.BOTS:
            ps, pc = f"Turn {g.turn + 1}  BOT TURN", RED
        else:
            ps, pc = "GAME ENDED", GRY
        self._t(ps, x, y, self.fmd, pc); y += 22
        self._sep(y); y += 10

        # ── Player stats ──────────────────────────────────────────────────────
        self._t("PLAYER", x, y, self.fmd, BLU); y += 20
        self._bar("HP", g.player.hp, g.player.stats.condition, GRN, x, y); y += 17
        self._bar("AP", g.player.ap, g.player.max_ap, CYN, x, y); y += 17
        self._t(
            f"STR:{g.player.stats.strength}  AGI:{g.player.stats.agility}"
            f"  SPD:{g.player.stats.speed}",
            x, y, self.fsm, WHT); y += 15
        fb = g.player.charges["fireball"]
        hl = g.player.charges["heal"]
        self._t(f"Fireball: {'*' * fb}{'·' * (3 - fb)} ({fb}/3)", x, y, self.fsm, ORG); y += 14
        self._t(f"Heal:     {'*' * hl}{'·' * (3 - hl)} ({hl}/3)", x, y, self.fsm, PNK); y += 14
        y += 4; self._sep(y); y += 10

        # ── Mode indicator ────────────────────────────────────────────────────
        MC = {Mode.NONE: GRY, Mode.MOVE: BLU, Mode.STRIKE: YLW,
              Mode.SHOOT: GRN, Mode.FIREBALL: ORG}
        self._t(f"Mode: {g.mode.value.upper()}", x, y, self.fmd, MC.get(g.mode, WHT))
        y += 26

        btn_top = y
        y += 3 * (30 + 8) + 6   # 3 button rows

        self._sep(y); y += 10

        # ── Enemies ───────────────────────────────────────────────────────────
        self._t("ENEMIES", x, y, self.fmd, RED); y += 20
        for b in game.bots:
            if b.alive:
                fg, _ = b.clr
                self._t(f"{b.name} ({b.x},{b.y})", x, y, self.fsm, fg); y += 13
                self._bar("", b.hp, b.stats.condition, fg, x, y, bw=110); y += 14
            else:
                self._t(f"{b.name} [dead]", x, y, self.fsm, (70, 70, 80)); y += 16

        y += 4; self._sep(y); y += 8

        # ── Combat log ────────────────────────────────────────────────────────
        self._t("LOG", x, y, self.fmd, GRY); y += 18
        visible = game.log.lines[-8:]
        for msg, clr in visible:
            self._t(msg, x, y, self.fsm, clr); y += 14

        # ── Hints ─────────────────────────────────────────────────────────────
        hy = WIN_H - 52
        self._sep(hy); hy += 5
        for hint in ["Arrows/WASD: move or strike dir",
                     "Click grid: shoot / fireball",
                     "ESC: cancel   E: end turn"]:
            self._t(hint, x, hy, self.fsm, (65, 65, 78)); hy += 14

        return btn_top

    def _buttons(self, game: Game):
        for btn in self._btns:
            active = btn["mode"] is not None and btn["mode"] == game.mode
            pygame.draw.rect(self.screen, DGRY, btn["rect"])
            border = WHT if active else (72, 72, 85)
            pygame.draw.rect(self.screen, border, btn["rect"], 2)
            lbl = self.fsm.render(btn["lbl"], True, btn["clr"])
            lx = btn["rect"].x + btn["rect"].w // 2 - lbl.get_width() // 2
            ly = btn["rect"].y + btn["rect"].h // 2 - lbl.get_height() // 2
            self.screen.blit(lbl, (lx, ly))

    def _overlay(self, text: str, clr: tuple):
        surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 175))
        self.screen.blit(surf, (0, 0))
        lbl = self.fxl.render(text, True, clr)
        self.screen.blit(lbl, (WIN_W // 2 - lbl.get_width() // 2,
                                WIN_H // 2 - lbl.get_height() // 2 - 20))
        sub = self.fmd.render("Press R to restart  |  ESC to quit", True, WHT)
        self.screen.blit(sub, (WIN_W // 2 - sub.get_width() // 2,
                                WIN_H // 2 + 32))

    # ── helpers ───────────────────────────────────────────────────────────────
    def _t(self, s: str, x: int, y: int, font, clr: tuple):
        self.screen.blit(font.render(s, True, clr), (x, y))

    def _sep(self, y: int):
        pygame.draw.line(self.screen, SEP, (PANEL_X, y), (PANEL_X + PANEL_W, y))

    def _bar(self, label: str, val: int, mx: int, clr: tuple,
             x: int, y: int, bw: int = PANEL_W):
        if label:
            l = self.fsm.render(f"{label}:{val:3d}", True, WHT)
            self.screen.blit(l, (x, y))
            x += 48; bw -= 48
        bw -= 4
        pygame.draw.rect(self.screen, DGRY, (x, y + 1, bw, 11))
        r = val / mx if mx else 0
        pygame.draw.rect(self.screen, clr, (x, y + 1, int(bw * r), 11))


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Top-Down Grid Game  —  Player vs Bots")
    clock = pygame.time.Clock()
    renderer = Renderer(screen)

    game = Game()
    bot_delay = 0

    DIRS = {
        pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
        pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
        pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
        pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
    }

    while True:
        dt = clock.tick(30)

        # ── bot turn pacing ───────────────────────────────────────────────────
        if game.phase == Phase.BOTS:
            bot_delay -= dt
            if bot_delay <= 0:
                game.run_bots()
                bot_delay = 550

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                gx = (mx - GX) // CELL_SIZE
                gy = (my - GY) // CELL_SIZE
                game.hover = (gx, gy) if game.grid.ok(gx, gy) else None

            elif event.type == pygame.KEYDOWN:
                key = event.key

                # restart / quit on game-over
                if game.phase in (Phase.WIN, Phase.LOSE):
                    if key == pygame.K_r:
                        game = Game()
                    elif key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    continue

                if game.phase != Phase.PLAYER:
                    continue

                # directional keys — used for Move and Strike
                if key in DIRS and game.mode in (Mode.MOVE, Mode.STRIKE):
                    dx, dy = DIRS[key]
                    if game.mode == Mode.MOVE:
                        game.player_move(game.player.x + dx, game.player.y + dy)
                    else:
                        game.player_strike(game.player.x + dx, game.player.y + dy)
                    continue

                # mode hotkeys
                if   key == pygame.K_m: game.mode = Mode.MOVE
                elif key == pygame.K_s: game.mode = Mode.STRIKE
                elif key == pygame.K_r: game.mode = Mode.SHOOT
                elif key == pygame.K_f: game.mode = Mode.FIREBALL
                elif key == pygame.K_h: game.player_heal()
                elif key in (pygame.K_e, pygame.K_RETURN): game.end_player_turn()
                elif key == pygame.K_ESCAPE: game.mode = Mode.NONE

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # button click
                handled = False
                for btn in renderer.button_rects():
                    if btn["rect"].collidepoint(pos):
                        if game.phase != Phase.PLAYER:
                            break
                        if btn["lbl"].startswith("Heal"):
                            game.player_heal()
                        elif btn["lbl"].startswith("End"):
                            game.end_player_turn()
                        elif btn["mode"] is not None:
                            game.mode = btn["mode"]
                        handled = True
                        break

                # grid click
                if not handled:
                    gx = (pos[0] - GX) // CELL_SIZE
                    gy = (pos[1] - GY) // CELL_SIZE
                    if game.grid.ok(gx, gy) and game.phase == Phase.PLAYER:
                        m = game.mode
                        if m == Mode.MOVE:
                            game.player_move(gx, gy)
                        elif m == Mode.STRIKE:
                            game.player_strike(gx, gy)
                        elif m == Mode.SHOOT:
                            game.player_shoot(gx, gy)
                        elif m == Mode.FIREBALL:
                            game.player_fireball(gx, gy)

        renderer.draw(game)
        pygame.display.flip()


if __name__ == "__main__":
    main()
