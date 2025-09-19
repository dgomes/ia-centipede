import asyncio
import logging
import random
from collections import deque
from unicodedata import name

from consts import KILL_CENTIPEDE_BODY_POINTS, TIMEOUT, Direction, HISTORY_LEN, Tiles
from mapa import Map

logger = logging.getLogger("Game")
logger.setLevel(logging.DEBUG)

INITIAL_SCORE = 0
GAME_SPEED = 10
MAP_SIZE = (48, 24)
FOOD_IN_MAP = 4

class Centipede:
    def __init__(self, player_name, x=1, y=1):
        self._name = player_name
        self._body = [(x, y)]
        self._spawn_pos = (x, y)
        self._direction: Direction = Direction.EAST
        self._history = deque(maxlen=HISTORY_LEN)
        self._score = 0
        self._alive = True
        self.lastkey = ""
        self.to_grow = 1
        self.range = 3

    def grow(self, amount=1):
        self.to_grow += amount
        self.to_grow = max(-len(self._body) + 1, self.to_grow)

    @property
    def head(self):
        return self._body[-1]

    @property
    def tail(self):
        return self._body[:-1]

    @property
    def body(self):
        return self._body

    @property
    def alive(self):
        return self._alive

    def kill(self):
        self._alive = False

    @property
    def name(self):
        return self._name

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value

    @property
    def history(self):
        return str(list(self._history))

    @property
    def direction(self):
        return self._direction

    @property
    def x(self):
        return self._pos[0]

    @property
    def y(self):
        return self._pos[1]

    @property
    def __str__(self) -> str:
        return f"{self.name}({self._pos})"

    def move(self, mapa, direction: Direction):
        if direction is None:
            return

        new_pos = mapa.calc_pos(self.head, direction, traverse=self._traverse)

        if new_pos == self.head or new_pos in self._body:
            # if we can't move to the new position, we crashed against a wall
            # or we are crashing against ourselves
            logger.debug(
                "Head %s can't move to %s with direction %s",
                self.head,
                new_pos,
                direction,
            )
            self.kill()
            return

        self._body.append(new_pos)
        if self.to_grow > 0:  # if we are growing
            self.to_grow -= 1
        elif self.to_grow < 0 and len(self._body) > 3:  # if we are shrinking
            self.to_grow += 1
            self._body.pop(0)
            self._body.pop(0)
        else:  # if we are simply moving
            self._body.pop(0)

        self._direction = direction
        self._history.append(new_pos)

    def collision(self, pos):
        return pos in self._body

    def take_hit(self, blast):
        if blast in self._body:
            index = self._body.index(blast)
            new_centipede = self._body[index + 1 :]
            if len(self._body) < 1:
                self.kill()
            else:
                return Centipede(self._name, *new_centipede[0])
        

    def _calc_dir(self, old_pos, new_pos):
        if old_pos[0] < new_pos[0]:
            return Direction.EAST
        elif old_pos[0] > new_pos[0]:
            return Direction.WEST
        elif old_pos[1] < new_pos[1]:
            return Direction.SOUTH
        elif old_pos[1] > new_pos[1]:
            return Direction.NORTH
        logger.error(
            "Can't calculate direction from %s to %s, please report as this is a bug",
            old_pos,
            new_pos,
        )
        return None

class BugBlaster:
    def __init__(self, x=1, y=1):
        self._pos = (x, y)
        self._score = 0
        self._alive = True
        self.lastkey = ""
        self._direction: Direction = Direction.EAST
    
    def move(self, mapa, direction: Direction):
        if direction is None:
            return
        
        if direction == Direction.NORTH:
            if self._pos[1] > 0:
                self._pos = (self._pos[0], self._pos[1] - 1)
        elif direction == Direction.SOUTH:
            if self._pos[1] < mapa.size[1] - 1:
                self._pos = (self._pos[0], self._pos[1] + 1)
        elif direction == Direction.WEST:
            if self._pos[0] > 0:
                self._pos = (self._pos[0] - 1, self._pos[1])
        elif direction == Direction.EAST:
            if self._pos[0] < mapa.size[0] - 1:
                self._pos = (self._pos[0] + 1, self._pos[1])
        self._direction = direction


class Mushroom:
    def __init__(self, x=1, y=1):
        self._pos = (x, y)
        self._health = 4

    def __str__(self):
        return f"Mushroom({self._pos}, health={self._health})"

    def take_damage(self):
        self._health -= 1

    def collision(self, pos):
        return pos == self._pos
   
    def exists(self):
        return self._health > 0
    
    @property
    def pos(self):
        return self._pos

    @property
    def health(self):
        return self.health 


def key2direction(key):
    if key == "w":
        return Direction.NORTH
    elif key == "a":
        return Direction.WEST
    elif key == "s":
        return Direction.SOUTH
    elif key == "d":
        return Direction.EAST
    return None


class Game:
    def __init__(self, level=1, timeout=TIMEOUT, size=MAP_SIZE, game_speed=GAME_SPEED):
        logger.info(f"Game(level={level})")
        self.initial_level = level
        self._game_speed = game_speed
        self._running = False
        self._timeout = timeout
        self._step = 0
        self._state = {}
        self._centipedes = []
        self._bug_blaster = {}
        self._blasts = []
        self._last_key = ""
        self.map = Map(size=size)

    @property
    def centipedes(self):
        return self._centipedes

    @property
    def bug_blaster(self):
        return self._bug_blaster

    @property
    def level(self):
        return self.map.level

    @property
    def running(self):
        return self._running

    @property
    def total_steps(self):
        return self._total_steps

    def start(self, players_names):
        logger.debug("Reset world")
        self._running = True
        self._centipedes = [Centipede(*self.map.spawn_centipede())]
        self._bug_blaster = {name: BugBlaster(*self.map.spawn_bug_blaster()) for name in players_names}

    def stop(self):
        logger.info("GAME OVER")
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, player_name, key):
        self._snakes[player_name].lastkey = key

    def update_bug_blaster(self):
        try:
            if not self._bug_blaster.exists():
                return  # if snake is dead, we don't need to update it  
            lastkey = self._last_key

            assert lastkey in "wasdp" or lastkey == ""

            # Update position
            self._bug_blaster.move(
                self.map,
                key2direction(lastkey)
                if lastkey in "wasd" and lastkey != ""
                else self._bug_blaster.direction,
            )

            # Shoot
            if lastkey == "p":
                self._blasts.append(self._bug_blaster.head)
                logger.info("BugBlaster <%s> fired a blast", self._bug_blaster)


        except AssertionError:
            logger.error("Invalid key <%s> pressed. Valid keys: w,a,s,d", lastkey)

        return True



    def collision(self):
        if (
            not self._running
        ):  # if game is not running, we don't need to check collisions
            return

        for centipede in self._centipedes:
            if not centipede.exists():
                continue

            # check collisions between snakes
            for centipede2 in self._centipedes:
                if not centipede2.exists():
                    continue
                if centipede != centipede2 and centipede2.collision(centipede.head):
                    centipede.reverse()
                    centipede2.reverse()
                    logger.info("Centipede <%s> collided with centipede <%s>", centipede.name, centipede2.name)


            # check collisions with mushrooms
            for mushroom in self.map.mushrooms:
                if not mushroom.exists():
                    continue
                if mushroom.collision(centipede.head):
                    centipede.reverse()

            # check collisions with blasters
            for blast in self._blasts:    
                if blast.collision(centipede.head):
                    r = centipede.take_hit(blast)
                    if r:
                        self._centipedes.append(r)
                        self.score += KILL_CENTIPEDE_BODY_POINTS
                        logger.info("Centipede <%s> was hit by a blast and split", centipede)



    async def next_frame(self):
        await asyncio.sleep(1.0 / self._game_speed)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug(f"[{self._step}] SCORE {name}: {self.bug_blaster.score}")

        for centipede in self._centipedes:
            if centipede.alive:
                centipede.move()
                
               
        self.update_bug_blaster()

        # update blasts
        self._blasts = [(x, y) for x, y in self._blasts if y > 0]

        self.collision()

        self._state = {
            "centipedes": [centipede for centipede in self._centipedes if centipede.alive],
            "bug_blaster": self._bug_blaster,
            "mushrooms": [mushroom for mushroom in self.map.mushrooms if mushroom.exists()],
            "blasts": self._blasts,
            "step": self._step,
            "timeout": self._timeout,
        }

        if all([not centipede.alive for centipede in self._centipedes]):
            self.stop()

        return self._state

    def info(self):
        return {
            "size": self.map.size,
            "map": self.map.map,
            "fps": self._game_speed,
            "timeout": self._timeout,
            "level": self.map.level,
        }
