from galaxy.api.types import GameTime

from dataclasses import dataclass
from time import time
from typing import Dict
import pickle


@dataclass
class _RunningGameInfo(object):
    game_id: str = None
    start_time: float = None

    def update_start_time(self):
        self.start_time = time()


class TimeTracker:
    def __init__(self, game_time_cache: str = None):
        self._running_games_dict: Dict[str, _RunningGameInfo] = {}
        self._game_time_cache = {}
        if game_time_cache:
            self._game_time_cache = pickle.loads(bytes.fromhex(game_time_cache))

    def start_tracking_game(self, game_id: str, start_time: float = time()) -> None:
        if game_id not in self._game_time_cache:
            self._game_time_cache[game_id]['time_played'] = 0
            self._game_time_cache[game_id]['last_played'] = start_time
        self._running_games_dict[game_id] = (_RunningGameInfo(game_id=game_id, start_time=(time() if not start_time else
                                                                                           start_time)))

    def stop_tracking_game(self, game_id: str) -> None:
        if game_id not in self._running_games_dict:
            raise GameNotTrackedException
        del self._running_games_dict[game_id]

    def get_tracked_time(self, game_id: str) -> GameTime:
        if game_id not in self._running_games_dict:
            raise GameNotTrackedException
        start_time = self._game_time_cache[game_id]['last_played']
        current_time = time()
        self._game_time_cache[game_id]['last_played'] = current_time
        minutes_passed = (current_time - start_time) / 60
        self._game_time_cache[game_id]['time_played'] += minutes_passed
        time_played = self._game_time_cache[game_id]['time_played']
        return GameTime(game_id, time_played=int(time_played), last_played_time=int(current_time))

    def get_time_cache(self) -> Dict[str, Dict[str, float]]:
        return self._game_time_cache

    def get_time_cache_hex(self) -> str:
        return pickle.dumps(self._game_time_cache).hex()


class GameNotTrackedException(Exception):
    pass
