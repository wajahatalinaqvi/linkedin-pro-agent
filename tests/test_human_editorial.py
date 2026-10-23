"""New visual treatments preserve source text and old layouts."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from writing_voice import choose_angle
from carousel.visual_storytelling import apply_visual_storytelling
from carousel.renderer import render_html

class HumanEditorialTests(unittest.TestCase):
    def test_angle_is_stable(self):
        self.assertEqual(choose_angle("a"),choose_angle("a"))

    def test_visuals_are_opt_in_and_keep_facts(self):
        base=[{"type":"cover","title":"Real detail on a platform update"},{"type":"cards","title":"Important findings","cards":[["1","Source verified", "Technical detail"],["2","Practical","Implication"],["3","Caveat","Limitation"]]},{"type":"comparison","title":"What changes"},{"type":"cards","title":"Implementation"},{"type":"timeline","title":"Build steps","events":[["1","Check requirements","Before development"],["2","Use documented endpoint","During implementation"],["3","Verify result","After implementation"]]},{"type":"closing","title":"Next actions"}]
        import copy
        v={"design_version":"studio-v2","slides":copy.deepcopy(base)}
        v["slides"][1]["visual_intent"]="editorial_insights"
        v["slides"][4]["visual_intent"]="process"
        changed=apply_visual_storytelling(v)
        self.assertEqual(changed,["insight_list","process_map"])
        html=render_html(v)
        self.assertIn("Technical detail",html)
        self.assertIn("Before development",html)
        self.assertIn("process-node",html)
        self.assertIn("insight-node",html)
        legacy={"slides":copy.deepcopy(base)}
        legacy["slides"][1]["visual_intent"]="editorial_insights"
        self.assertEqual(apply_visual_storytelling(legacy),[])
        self.assertEqual(legacy["slides"][1]["type"],"cards")

if __name__=="__main__":
    unittest.main()
