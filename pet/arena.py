"""宠物竞技场与排位系统"""
from dataclasses import dataclass, field

RANK_ORDER = ["bronze", "silver", "gold", "platinum", "diamond", "master", "king"]

# 赛季奖励按段位阶梯发放，王者有专属奖励
SEASON_REWARDS = {
    "bronze": {"gold": 100, "gems": 0},
    "silver": {"gold": 300, "gems": 10},
    "gold": {"gold": 600, "gems": 30},
    "platinum": {"gold": 1000, "gems": 60},
    "diamond": {"gold": 2000, "gems": 120},
    "master": {"gold": 4000, "gems": 250},
    "king": {"gold": 8000, "gems": 500, "exclusive_title": "王者之风", "exclusive_skin": "king_arena"},
}

BASE_WIN_POINTS = 20
BASE_LOSE_POINTS = -10
# 每相差一个大段，胜负积分增减的幅度
RANK_GAP_POINT_STEP = 5


@dataclass
class Player:
    pid: str
    name: str
    rank: str = "bronze"
    pet_power: int = 1000
    pet_level: int = 1
    points: int = 0
    placement_played: int = 0
    quit_count: int = 0
    banned_until_season: int = -1


class ArenaSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}
        # 定级赛场数（新赛季默认5场）
        self.placement_matches: int = 5
        # 战斗记录（保存最近20场）
        self.battle_records: list = []
        self.max_battle_records: int = 20
        # 匹配限制：战力差距 / 等级差距 / 段位差距（大段数）
        self.max_power_gap: int = 3000
        self.max_level_gap: int = 10
        self.rank_gap_limit: int = 2
        # 秒退惩罚：扣双倍基础负分，多次秒退禁赛
        self.quit_penalty_points: int = BASE_LOSE_POINTS * 2
        self.quit_ban_threshold: int = 3
        # 赛季结算：积分清零（也可配置为按比例折算）
        self.season_reset_type: str = "reset_to_zero"
        self.season_reset_ratio: float = 0.0
        self.settlement_period_days: int = 3
        self.current_season: int = 1

    # ---- bug1/bug7: 综合匹配（段位+战力+等级），差距过大不匹配 ----
    def can_match(self, p1: Player, p2: Player) -> bool:
        rank_gap = abs(self._rank_index(p1.rank) - self._rank_index(p2.rank))
        if rank_gap > self.rank_gap_limit:
            return False
        if abs(p1.pet_power - p2.pet_power) > self.max_power_gap:
            return False
        if abs(p1.pet_level - p2.pet_level) > self.max_level_gap:
            return False
        return True

    def find_match(self, player: Player, candidates: list | None = None) -> str:
        for other in (candidates or []):
            if other.pid != player.pid and self.can_match(player, other):
                return other.pid
        return "no_match"

    # ---- bug2: 定级赛 ----
    def get_placement_matches(self) -> int:
        return self.placement_matches

    def finish_placements(self, player: Player, wins: int, avg_performance: float) -> str:
        """根据定级赛表现确定初始段位"""
        score = wins + avg_performance
        if score >= 5.5:
            player.rank = "platinum"
        elif score >= 4.0:
            player.rank = "gold"
        elif score >= 2.5:
            player.rank = "silver"
        else:
            player.rank = "bronze"
        player.placement_played = self.placement_matches
        return player.rank

    # ---- bug3: 积分按对手段位与战斗表现计算 ----
    def calculate_points(self, win: bool, opponent_rank: str, performance: float,
                         to_rank: str = "gold") -> int:
        gap = self._rank_index(opponent_rank) - self._rank_index(to_rank)
        perf_bonus = int(round(performance * 5))
        if win:
            # 赢高段位加分多，赢低段位加分少
            return BASE_WIN_POINTS + gap * RANK_GAP_POINT_STEP + perf_bonus
        # 输给高段位扣分少，输给低段位扣分多
        return BASE_LOSE_POINTS - gap * RANK_GAP_POINT_STEP + perf_bonus

    # ---- bug4: 段位阶梯奖励 ----
    def get_season_reward(self, rank: str) -> dict:
        return dict(SEASON_REWARDS.get(rank, SEASON_REWARDS["bronze"]))

    # ---- bug5: 战斗记录保存最近20场 ----
    def record_battle(self, record: dict) -> None:
        self.battle_records.append(record)
        if len(self.battle_records) > self.max_battle_records:
            self.battle_records = self.battle_records[-self.max_battle_records:]

    def get_battle_history(self, player_id: str) -> list:
        records = [r for r in self.battle_records
                   if r.get("player_id") in (None, player_id) or player_id in (
                       r.get("player_id"), r.get("p1"), r.get("p2"))]
        return records[-self.max_battle_records:]

    def get_battle_detail(self, battle_id) -> dict | None:
        for r in self.battle_records:
            if r.get("id") == battle_id:
                return r
        return None

    # ---- bug6: 秒退扣分惩罚，多次秒退禁赛 ----
    def get_quit_penalty(self) -> int:
        return self.quit_penalty_points

    def apply_quit(self, player: Player) -> int:
        player.points += self.quit_penalty_points
        player.quit_count += 1
        if player.quit_count >= self.quit_ban_threshold:
            player.banned_until_season = self.current_season + 1
        return self.quit_penalty_points

    def is_banned(self, player: Player) -> bool:
        return player.banned_until_season >= self.current_season

    # ---- bug7: 跨段位匹配差距限制 ----
    def get_rank_gap_limit(self) -> int:
        return self.rank_gap_limit

    # ---- bug8: 赛季结束积分清零/折算 + 结算期 ----
    def get_season_reset_type(self) -> str:
        return self.season_reset_type

    def end_season(self) -> dict:
        rewards = {pid: self.get_season_reward(p.rank) for pid, p in self.players.items()}
        for p in self.players.values():
            if self.season_reset_type == "reset_to_zero":
                p.points = 0
            elif self.season_reset_type == "scale":
                p.points = int(p.points * self.season_reset_ratio)
            p.placement_played = 0
            p.quit_count = 0
        self.current_season += 1
        return {"rewards": rewards, "settlement_days": self.settlement_period_days}

    @staticmethod
    def _rank_index(rank: str) -> int:
        return RANK_ORDER.index(rank) if rank in RANK_ORDER else 0
