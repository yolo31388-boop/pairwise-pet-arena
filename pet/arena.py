"""宠物竞技场与排位系统"""
from dataclasses import dataclass, field

RANKS = ["bronze", "silver", "gold", "platinum", "diamond", "master", "king"]
RANK_INDEX = {r: i for i, r in enumerate(RANKS)}

# 段位阶梯奖励，王者有专属奖励
SEASON_REWARDS = {
    "bronze": {"gold": 100, "gems": 0},
    "silver": {"gold": 300, "gems": 10},
    "gold": {"gold": 600, "gems": 30},
    "platinum": {"gold": 1000, "gems": 60},
    "diamond": {"gold": 1500, "gems": 100},
    "master": {"gold": 2500, "gems": 200},
    "king": {"gold": 5000, "gems": 500, "exclusive": "king_avatar_frame"},
}

# 基础胜/负积分
BASE_WIN_POINTS = 20
BASE_LOSE_POINTS = -10
# 每相差一个大段的积分修正
RANK_DIFF_BONUS = 5


@dataclass
class Player:
    pid: str
    name: str
    rank: str = "bronze"
    pet_power: int = 1000
    pet_level: int = 1
    points: int = 0
    placement_done: int = 0
    quit_count: int = 0
    banned: bool = False


class ArenaSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}
        # 定级赛场数（默认5场）
        self.placement_matches: int = 5
        # 战斗记录（每个玩家保留最近20场）
        self.battle_records: list[dict] = []
        self.max_battle_records: int = 20
        # 匹配限制：战力差距、等级差距、段位差距（默认不超过2个大段）
        self.max_power_gap: int = 3000
        self.max_level_gap: int = 10
        self.rank_gap_limit: int = 2
        # 秒退惩罚：扣双倍积分，多次秒退禁赛
        self.quit_penalty_multiplier: int = 2
        self.quit_ban_threshold: int = 3
        # 赛季结算：清零或按比例折算，有结算期
        self.season_reset_type: str = "reset"  # "reset" 清零 / "scale" 按比例折算
        self.season_reset_scale: float = 0.5
        self.settlement_days: int = 3

    # ---------- 匹配 ----------
    def can_match(self, p1: Player, p2: Player) -> bool:
        """按段位+战力+等级综合判断两名玩家是否可匹配。"""
        if abs(RANK_INDEX[p1.rank] - RANK_INDEX[p2.rank]) > self.rank_gap_limit:
            return False
        if abs(p1.pet_power - p2.pet_power) > self.max_power_gap:
            return False
        if abs(p1.pet_level - p2.pet_level) > self.max_level_gap:
            return False
        return True

    def find_match(self, player: Player) -> str:
        """在已注册玩家中寻找综合条件匹配的对手。"""
        for other in self.players.values():
            if other.pid == player.pid or other.banned:
                continue
            if self.can_match(player, other):
                return other.pid
        return "no_match"

    # ---------- 定级赛 ----------
    def get_placement_matches(self) -> int:
        return self.placement_matches

    def finish_placement(self, player: Player, wins: int, avg_performance: float) -> str:
        """定级赛结束后根据胜场和表现确定初始段位。"""
        score = wins + avg_performance
        if score >= 5.5:
            player.rank = "platinum"
        elif score >= 4.0:
            player.rank = "gold"
        elif score >= 2.5:
            player.rank = "silver"
        else:
            player.rank = "bronze"
        player.placement_done = self.placement_matches
        return player.rank

    # ---------- 积分 ----------
    def calculate_points(self, win: bool, opponent_rank: str, performance: float) -> int:
        """按对手段位（赢高分多、赢低分少）和战斗表现计算积分。"""
        base = BASE_WIN_POINTS if win else BASE_LOSE_POINTS
        # 对手越强，赢分越多、输分越少
        rank_bonus = RANK_INDEX.get(opponent_rank, 0) * RANK_DIFF_BONUS
        # 战斗表现修正（performance 以 1.0 为基准）
        perf_bonus = int(round((performance - 1.0) * 10))
        if win:
            return base + rank_bonus + perf_bonus
        return base - rank_bonus // 2 + perf_bonus

    # ---------- 赛季奖励 ----------
    def get_season_reward(self, rank: str) -> dict:
        """按段位阶梯发放奖励，王者有专属奖励。"""
        return dict(SEASON_REWARDS.get(rank, SEASON_REWARDS["bronze"]))

    # ---------- 战斗记录 ----------
    def record_battle(self, player_id: str, record: dict) -> None:
        """保存战斗记录，每个玩家最多保留最近20场。"""
        entry = dict(record)
        entry["player_id"] = player_id
        self.battle_records.append(entry)
        mine = [r for r in self.battle_records if r.get("player_id") == player_id]
        if len(mine) > self.max_battle_records:
            excess = len(mine) - self.max_battle_records
            kept, removed = [], 0
            for r in self.battle_records:
                if r.get("player_id") == player_id and removed < excess:
                    removed += 1
                    continue
                kept.append(r)
            self.battle_records = kept

    def get_battle_history(self, player_id: str) -> list:
        """查看玩家最近20场战斗记录详情。"""
        return [r for r in self.battle_records
                if r.get("player_id", player_id) == player_id][-self.max_battle_records:]

    # ---------- 秒退惩罚 ----------
    def get_quit_penalty(self) -> int:
        """秒退扣分（默认双倍基础负分）。"""
        return BASE_LOSE_POINTS * self.quit_penalty_multiplier

    def apply_quit(self, player: Player) -> int:
        """对秒退玩家扣分，多次秒退禁赛。"""
        penalty = self.get_quit_penalty()
        player.points += penalty
        player.quit_count += 1
        if player.quit_count >= self.quit_ban_threshold:
            player.banned = True
        return penalty

    # ---------- 跨段位限制 ----------
    def get_rank_gap_limit(self) -> int:
        return self.rank_gap_limit

    # ---------- 赛季结算 ----------
    def get_season_reset_type(self) -> str:
        return self.season_reset_type

    def settle_season(self, player: Player) -> dict:
        """赛季结算：发放段位奖励，积分按规则清零或折算，进入结算期。"""
        reward = self.get_season_reward(player.rank)
        if self.season_reset_type == "scale":
            player.points = int(player.points * self.season_reset_scale)
        else:
            player.points = 0
        player.placement_done = 0
        player.quit_count = 0
        player.banned = False
        return {"reward": reward, "points": player.points, "settlement_days": self.settlement_days}
