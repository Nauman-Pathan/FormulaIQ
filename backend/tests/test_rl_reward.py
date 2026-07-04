"""
Tests for rl_strategy/reward.py
Tests compute_step_reward and compute_terminal_reward with sample inputs.
Pure python — no DB, network, or ML model needed.
"""
import pytest
from rl_strategy.reward import compute_step_reward, compute_terminal_reward


# ── compute_step_reward ───────────────────────────────────────────────────────

class TestComputeStepReward:

    def _prev(self, **kwargs):
        base = {"tyre_degradation": 0.3, "current_position": 10, "tyre_age": 12}
        base.update(kwargs)
        return base

    def _next(self, **kwargs):
        base = {"tyre_degradation": 0.35, "current_position": 10}
        base.update(kwargs)
        return base

    def test_returns_float(self):
        r = compute_step_reward(0, self._prev(), self._next(), False, False)
        assert isinstance(r, float)

    def test_position_gain_gives_positive_reward(self):
        """Gaining from P10 → P8 should give positive position reward."""
        prev = self._prev(current_position=10)
        nxt = self._next(current_position=8)
        r = compute_step_reward(0, prev, nxt, False, False)
        assert r > 0

    def test_position_loss_gives_negative_component(self):
        """Losing from P8 → P12 (pit stop) should yield lower reward than staying."""
        prev = self._prev(current_position=8)
        nxt_stay = self._next(current_position=8)
        nxt_pit = self._next(current_position=12)
        r_stay = compute_step_reward(0, prev, nxt_stay, False, False)
        r_pit = compute_step_reward(1, prev, nxt_pit, True, False)
        # Staying out on clean tyres (no cliff) should beat losing 4 positions in a pit
        assert r_stay > r_pit

    def test_safety_car_pit_bonus_applied(self):
        """Pitting under SC should reward +10 vs normal pit penalty of -5."""
        prev = self._prev(tyre_age=15, tyre_degradation=0.65)
        nxt = self._next(current_position=10)
        sc_reward = compute_step_reward(1, prev, nxt, True, was_safety_car=True)
        normal_reward = compute_step_reward(1, prev, nxt, True, was_safety_car=False)
        assert sc_reward > normal_reward

    def test_early_pit_penalty_applied(self):
        """Pitting with tyre_age < 8 should be penalised by -20."""
        prev = self._prev(tyre_age=5, tyre_degradation=0.20)
        nxt = self._next(current_position=10)
        r = compute_step_reward(1, prev, nxt, True, False)
        # Position unchanged, so only penalties apply → should be negative
        assert r < 0

    def test_tyre_cliff_penalty_applied(self):
        """Staying out (action=0) with >80% degradation should be heavily penalised."""
        prev = self._prev(tyre_degradation=0.55)
        nxt = self._next(tyre_degradation=0.92)  # past cliff
        r = compute_step_reward(0, prev, nxt, False, False)
        assert r < 0

    def test_extreme_degradation_gives_large_penalty(self):
        """>95% degradation should trigger -50 penalty."""
        prev = self._prev(tyre_degradation=0.85)
        nxt = self._next(tyre_degradation=0.97)
        r = compute_step_reward(0, prev, nxt, False, False)
        assert r <= -50.0

    def test_sweet_spot_pit_reward(self):
        """Pitting when degradation is between 50-80% should get +15 bonus."""
        prev = self._prev(tyre_age=20, tyre_degradation=0.65)
        nxt = self._next(current_position=10)
        r = compute_step_reward(1, prev, nxt, True, False)
        # Has sweet spot bonus (+15) and normal pit penalty (-5): net should be > -5
        assert r > -5

    def test_healthy_tyre_stay_out_bonus(self):
        """Staying out (action=0) with <50% degradation gives small +1 bonus."""
        prev = self._prev(tyre_degradation=0.30)
        nxt = self._next(tyre_degradation=0.35, current_position=10)
        r = compute_step_reward(0, prev, nxt, False, False)
        # Position unchanged (+0), no penalties, +1 bonus
        assert r >= 1.0


# ── compute_terminal_reward ───────────────────────────────────────────────────

class TestComputeTerminalReward:

    def test_returns_float(self):
        r = compute_terminal_reward(5, 10)
        assert isinstance(r, float)

    def test_win_gives_highest_reward(self):
        r_win = compute_terminal_reward(1, 5)
        r_second = compute_terminal_reward(2, 5)
        assert r_win > r_second

    def test_podium_bonus_applied(self):
        r_podium = compute_terminal_reward(3, 10)
        r_fourth = compute_terminal_reward(4, 10)
        assert r_podium > r_fourth

    def test_points_finish_bonus_applied(self):
        r_points = compute_terminal_reward(10, 15)
        r_no_points = compute_terminal_reward(11, 15)
        assert r_points > r_no_points

    def test_positions_gained_reward(self):
        """Starting P10 and finishing P5 should score better than finishing P10."""
        r_gained = compute_terminal_reward(5, 10)
        r_same = compute_terminal_reward(10, 10)
        assert r_gained > r_same

    def test_positions_lost_penalises_reward(self):
        """Finishing worse than starting position reduces reward."""
        r_gained = compute_terminal_reward(8, 10)
        r_lost = compute_terminal_reward(15, 10)
        assert r_gained > r_lost

    def test_positional_score_component(self):
        """P1 score = 21-1=20 * 10 = 200 positional points."""
        # Terminal reward for P1 starting P1: win bonus + pos_score + 0 net_gained
        r = compute_terminal_reward(1, 1)
        # 200 (win) + 20*10 (pos_score) + 0 = 400
        assert r == pytest.approx(400.0)

    def test_last_place_reward_still_positive(self):
        """Even P20 should have some positive reward from positional score."""
        r = compute_terminal_reward(20, 20)
        # pos_score = max(0, 21-20)=1 * 10=10, net_gained=0
        assert r >= 10.0
