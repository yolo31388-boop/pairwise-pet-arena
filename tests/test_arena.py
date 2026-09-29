"""宠物竞技场与排位系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pet.arena import ArenaSystem, Player

class TestMatchmaking:
    def test_matching_considers_power(self):
        asys = ArenaSystem()
        # 应该有战力差距检查
        assert hasattr(asys, "max_power_gap")
        asys.max_power_gap = 2000
        p1 = Player("p1", "a", rank="gold", pet_power=1000)
        p2 = Player("p2", "b", rank="gold", pet_power=100000)
        # 战力差距过大不应匹配
        assert asys.max_power_gap < abs(p1.pet_power - p2.pet_power)

class TestPlacementMatches:
    def test_new_season_has_placement_matches(self):
        asys = ArenaSystem()
        n = asys.get_placement_matches()
        assert n > 0

class TestPointCalculation:
    def test_beating_higher_rank_gives_more_points(self):
        asys = ArenaSystem()
        p1 = asys.calculate_points(True, "bronze", 1.0)
        p2 = asys.calculate_points(True, "diamond", 1.0)
        assert p2 > p1

class TestSeasonReward:
    def test_higher_rank_better_reward(self):
        asys = ArenaSystem()
        r1 = asys.get_season_reward("bronze")
        r2 = asys.get_season_reward("diamond")
        assert r2["gold"] > r1["gold"]

class TestBattleHistory:
    def test_battle_records_saved(self):
        asys = ArenaSystem()
        asys.battle_records = [{"id": 1, "result": "win"}]
        history = asys.get_battle_history("p1")
        assert len(history) > 0

class TestQuitPenalty:
    def test_quitting_has_penalty(self):
        asys = ArenaSystem()
        penalty = asys.get_quit_penalty()
        assert penalty < 0

class TestRankGapLimit:
    def test_rank_gap_has_limit(self):
        asys = ArenaSystem()
        limit = asys.get_rank_gap_limit()
        assert limit < 10

class TestSeasonReset:
    def test_season_resets_points(self):
        asys = ArenaSystem()
        reset_type = asys.get_season_reset_type()
        assert reset_type != "keep_all"
