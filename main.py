from __future__ import annotations
import berserk
from pprint import pprint
import time

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

def block_stats():
    block_counter = 0
    block_and_ban_counter = 0
    opponents = set()
    games = client.games.export_by_player(
        user, as_pgn=False, perf_type="rapid,classical", rated=True,
        until=round(time.time() * 1000 - 2_628_000_000) # time in ms for a month ago
    )
    for game in games:
        white, black = (game['players'][colour]['user']['id'] for colour in ('white', 'black'))
        opponent = black if white.lower() == user.lower() else white
        if opponent in opponents:
            continue
        opponents.add(opponent)
        if is_blocked(opponent):
            block_counter += 1
            print(f"Blocked {opponent} after playing", end='')
            if is_banned(opponent):
                block_and_ban_counter += 1
                print(' and they got banned', end='')
            print(f"\npercentage of those blocked who were banned: " +
                  f"{block_and_ban_counter / block_counter * 100}%\n")

def main():
    block_stats()

if __name__ == '__main__':
    main()