from collections import Counter
import sys
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_profile_stats import render_languages, render_player_stats

NS = {"svg": "http://www.w3.org/2000/svg"}


class StatsTests(unittest.TestCase):
    def test_all_languages_are_represented_when_legend_is_full(self):
        counts = Counter({"TypeScript": 14, "Python": 3, "Rust": 2, "Swift": 2,
                          "HTML": 1, "Vue": 1, "JavaScript": 1})
        svg = ET.fromstring(render_languages(counts))
        bars = svg.findall(".//svg:g[@clip-path]/svg:rect", NS)
        self.assertEqual(len(bars), 6)
        self.assertAlmostEqual(sum(float(bar.get("width")) for bar in bars), 447, places=1)
        self.assertAlmostEqual(float(bars[0].get("width")), 447 * 14 / 24, places=2)
        self.assertAlmostEqual(float(bars[-1].get("width")), 447 * 2 / 24, places=2)
        self.assertIn("Other", [text.text for text in svg.findall(".//svg:text", NS)])
        self.assertIn("Vue: 1", svg.find("svg:desc", NS).text)

    def test_equal_counts_have_stable_order(self):
        self.assertEqual(render_languages(Counter({"Vue": 1, "HTML": 1})),
                         render_languages(Counter({"HTML": 1, "Vue": 1})))

    def test_empty_language_data_is_a_valid_card(self):
        svg = ET.fromstring(render_languages(Counter()))
        self.assertEqual(svg.find("svg:desc", NS).text, "No language data available")
        self.assertEqual(svg.findall(".//svg:g[@clip-path]/svg:rect", NS), [])

    def test_labels_are_escaped_and_long_usernames_fit(self):
        username = "a" * 39
        svg = ET.fromstring(render_player_stats(username, 0, 0, 0))
        label = svg.find(".//svg:text[@text-anchor='end']", NS).text
        self.assertLessEqual(len(label), 17)
        self.assertIn(username, svg.find("svg:desc", NS).text)
        escaped = ET.fromstring(render_languages(Counter({"A&B<C": 1})))
        self.assertIn("A&B<C", escaped.find("svg:desc", NS).text)


if __name__ == "__main__":
    unittest.main()
