"""宠物竞技场与排位系统 - 含8个bug"""
from dataclasses import dataclass, field

@dataclass
class Player:
    pid: str
    name: str
    rank: str = "bronze"
    pet_power: int = 1000
    pet_level: int = 1

class ArenaSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.placement_matches: int = 0  # bug2: 无定级赛
        self.battle_records: list = []  # bug5: 不保存

    def find_match(self, player: Player) -> str:
        # bug1: 只看段位
        return "matched"

    def get_placement_matches(self) -> int:
        # bug2: 无定级赛
        return 0

    def calculate_points(self, win: bool, opponent_rank: str, performance: float) -> int:
        # bug3: 只看胜负
        return 20 if win else -10

    def get_season_reward(self, rank: str) -> dict:
        # bug4: 固定奖励
        return {"gold": 100}

    def get_battle_history(self, player_id: str) -> list:
        # bug5: 不保存
        return []

    def get_quit_penalty(self) -> int:
        # bug6: 秒退不扣分
        return 0

    def get_rank_gap_limit(self) -> int:
        # bug7: 无限制
        return 999

    def get_season_reset_type(self) -> str:
        # bug8: 不清零
        return "keep_all"
