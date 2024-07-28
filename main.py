from __future__ import annotations
import berserk
from pprint import pprint
from enum import Enum, auto
from dataclasses import dataclass
from itertools import product
from typing import Optional
from datetime import datetime, timedelta
from pytz import UTC

class Colour(Enum):
    WHITE = 'white'
    BLACK = 'black'

class TC(Enum):
    RAPID = 'rapid'
    CLASSICAL = 'classical'

class Result(Enum):
    WIN = auto()
    DRAW = auto()
    LOSE = auto()

@dataclass
class Performance:
    result: Optional[Result]
    opp_rating: float
    colour: Colour
    tc: TC

    def performance_val(self) -> Optional[float]:
        if self.result is None:
            return None
        addend = {Result.WIN: 400, Result.DRAW: 0, Result.LOSE: -400}[self.result]
        return self.opp_rating + addend

class Performances:
    def __init__(self):
        self._performances: list[Performance] = []

    def add_performance(self, performance: Performance) -> None:
        if performance.performance_val() is None:
            return
        self._performances.append(performance)

    def get_average_performance(self, colour: Colour, tc: TC) -> float:
        performances = [p.performance_val() for p in self._performances
                        if p.colour == colour and p.tc == tc]
        if not performances:
            return 0
        return round(sum(performances) / len(performances), 2)

def read_single_line(filename) -> str:
    with open(filename) as f:
        return f.readline().strip('\n')

session = berserk.TokenSession(read_single_line('api-key.txt'))
client = berserk.Client(session=session)
user = read_single_line('username.txt')

def is_blocked(username: str) -> bool:
    """Returns whether `user` is blocking `username`."""
    return client.users.get_public_data(username).get('blocking', False)

def is_banned(username: str) -> bool:
    return client.users.get_public_data(username).get('tosViolation', False)

def classical_rapid_stats():
    block_counter = 0
    block_and_ban_counter = 0
    performances = Performances()
    opponents = set()
    games = client.games.export_by_player(
        user, as_pgn=False, perf_type="rapid,classical", rated=True
    )
    for i, game in enumerate(games):
        white, black = (game['players'][colour] for colour in ('white', 'black'))
        is_user_white = white['user']['id'].lower() == user.lower()
        opponent = black if is_user_white else white
        opponent_id = opponent['user']['id']
        result = (Result.DRAW if game['status'] == 'draw' else
                  None if 'winner' not in game else
                  Result.WIN if (game.get('winner') == 'white') == is_user_white else
                  Result.LOSE)
        performances.add_performance(
            Performance(
                result, opponent['rating'], Colour.WHITE if is_user_white else Colour.BLACK,
                TC(game['perf'])
            )
        )
        if i % 100 == 0:
            print('\n')
            for colour, tc in product(Colour, TC):
                print(f"Average performance for playing {colour.value} in {tc.value} is " +
                      f"{performances.get_average_performance(colour, tc)}")

        if (opponent_id in opponents or
            UTC.localize(datetime.now() - timedelta(weeks=4)) < game['createdAt']):
            continue
        opponents.add(opponent_id)
        if is_blocked(opponent_id):
            block_counter += 1
            print(f"\nBlocked {opponent_id} after playing", end='')
            if is_banned(opponent_id):
                block_and_ban_counter += 1
                print(' and they got banned', end='')
            print(f"\npercentage of those blocked who were banned: " +
                  f"{block_and_ban_counter / block_counter * 100}%\n")

def main():
    classical_rapid_stats()

if __name__ == '__main__':
    main()