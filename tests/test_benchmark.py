import unittest
from benchmark import POLICIES, simulate_scenario
from generate_dataset import generate_scenarios


def small_scenario():
    return {"scenario_id": "test_case", "seed": 1, "action_types": "BSSSSB", "revoke_at": 2}


class BenchmarkTests(unittest.TestCase):
    def test_generator_is_deterministic(self):
        self.assertEqual(list(generate_scenarios(17, 5)), list(generate_scenarios(17, 5)))

    def test_generator_has_sensitive_action_after_revocation(self):
        for seed in (17, 29, 43):
            for row in generate_scenarios(seed, 50):
                self.assertIn("S", row["action_types"][row["revoke_at"]:])

    def test_check_once_exposes_stale_authority(self):
        r = simulate_scenario(small_scenario(), "check_once")
        self.assertEqual(r["unauthorized_side_effects"], 3)
        self.assertEqual(r["blocked_revoked_sensitive"], 0)

    def test_per_sensitive_blocks_revoked_actions(self):
        r = simulate_scenario(small_scenario(), "per_sensitive")
        self.assertEqual(r["unauthorized_side_effects"], 0)
        self.assertEqual(r["blocked_revoked_sensitive"], 3)

    def test_push_revocation_blocks_revoked_actions(self):
        r = simulate_scenario(small_scenario(), "push_revoke")
        self.assertEqual(r["unauthorized_side_effects"], 0)
        self.assertEqual(r["blocked_revoked_sensitive"], 3)
        self.assertEqual(r["revocation_notifications"], 1)

    def test_periodic_policy_catches_at_next_checkpoint(self):
        r = simulate_scenario(small_scenario(), "periodic_3")
        self.assertEqual(r["unauthorized_side_effects"], 1)
        self.assertEqual(r["blocked_revoked_sensitive"], 2)

    def test_all_policies_complete_authorized_work(self):
        for policy in POLICIES:
            self.assertEqual(simulate_scenario(small_scenario(), policy)["authorized_work_completion_rate"], 1.0)

    def test_unknown_policy_fails(self):
        with self.assertRaises(ValueError):
            simulate_scenario(small_scenario(), "unknown")


if __name__ == "__main__":
    unittest.main()
