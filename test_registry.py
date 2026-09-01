import unittest

import registry


class RegisterActionsTests(unittest.TestCase):
    def setUp(self):
        registry._registrations.clear()

    def test_bare_string_actions_pass_through_unchanged(self):
        registry.register(
            {"id": "s1", "base_url": "http://x", "actions": ["start", "stop"]}
        )
        self.assertEqual(registry.get("s1")["actions"], ["start", "stop"])

    def test_parameterized_action_dict_passes_through_unchanged(self):
        action = {
            "name": "apply_preset",
            "label": "Apply preset",
            "params": [{"name": "preset", "type": "enum", "options": ["casual"]}],
        }
        registry.register({"id": "s1", "base_url": "http://x", "actions": [action]})
        self.assertEqual(registry.get("s1")["actions"], [action])

    def test_malformed_action_dict_dropped(self):
        registry.register(
            {"id": "s1", "base_url": "http://x", "actions": [{"label": "no name"}]}
        )
        self.assertEqual(registry.get("s1")["actions"], [])

    def test_mixed_actions_list(self):
        action = {"name": "apply_preset", "params": []}
        registry.register(
            {"id": "s1", "base_url": "http://x", "actions": ["start", action]}
        )
        self.assertEqual(registry.get("s1")["actions"], ["start", action])

    def test_action_names_extracts_names_from_mixed_list(self):
        action = {"name": "apply_preset", "params": []}
        registry.register(
            {"id": "s1", "base_url": "http://x", "actions": ["start", action]}
        )
        self.assertEqual(registry.action_names(registry.get("s1")), {"start", "apply_preset"})


class RegisterStatsTests(unittest.TestCase):
    def setUp(self):
        registry._registrations.clear()

    def test_stats_passthrough(self):
        stats = [{"label": "Map", "value": "de_nuke"}]
        registry.register({"id": "s1", "base_url": "http://x", "stats": stats})
        self.assertEqual(registry.get("s1")["stats"], stats)

    def test_stats_defaults_to_empty_list_when_absent(self):
        registry.register({"id": "s1", "base_url": "http://x"})
        self.assertEqual(registry.get("s1")["stats"], [])

    def test_stats_defaults_to_empty_list_when_not_a_list(self):
        registry.register({"id": "s1", "base_url": "http://x", "stats": "nope"})
        self.assertEqual(registry.get("s1")["stats"], [])


if __name__ == "__main__":
    unittest.main()
