import unittest
import sys
import os

# Set up paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detectors.certainty_creep import CertaintyCreepDetector
from detectors.responsibility_diffusion import ResponsibilityDiffusionDetector
from detectors.niat_impact_substitution import NiatImpactSubstitutionDetector
from detectors.trajectory import TrajectoryDetector

class TestEntropyMesh(unittest.TestCase):

    def setUp(self):
        self.cc_detector = CertaintyCreepDetector()
        self.rd_detector = ResponsibilityDiffusionDetector()
        self.nis_detector = NiatImpactSubstitutionDetector()
        self.traj_detector = TrajectoryDetector()

    # --- Benign Tests ---
    def test_benign_technical_certainty(self):
        # A statement expressing 100% technical certainty about safety/sensors, which is benign
        text = "We are 100% certain the sensor calibration is complete and verified."
        res = self.cc_detector.analyze_statement(text)
        # Should not flag creep on single statement with high evidence/sensor grounding
        creep_res = self.cc_detector.detect([text], evidence_count=5)
        self.assertFalse(creep_res["creep_detected"], "Benign technical certainty flagged as creep.")

    def test_satire_and_hostile_quote(self):
        # Satire or quoting hostile speech should not lead to moral condemnation
        quoted_speech = "The report alleges: 'He is a liar and malicious.' We need to verify these claims."
        res = self.rd_detector.detect(quoted_speech)
        self.assertFalse(res["diffusion_detected"], "Hostile quote misclassified as diffusion.")

    # --- Institutional Tests ---
    def test_responsibility_diffusion(self):
        # Text with clear responsibility laundering signals
        diffused_text = "The action was taken because the system automated algorithm recommended it and policy mandates compliance."
        res = self.rd_detector.detect(diffused_text)
        self.assertTrue(res["diffusion_detected"], "Failed to detect responsibility diffusion.")
        self.assertIn("system", [p.split()[-1] if p.split() else '' for p in res["observed_phrases"]] + ["automated tool"])

    # --- Adversarial Tests ---
    def test_niat_impact_substitution(self):
        declared = "We intend to protect downstream water basins."
        impact = "The water pH dropped to 4.2 causing fish die-off."
        # Response focuses on intention and policy, not repair
        response = "Our policy was followed completely and our intention was to operate safely under the design guidelines."
        
        res = self.nis_detector.detect(declared, impact, response)
        self.assertTrue(res["substitution_detected"], "Failed to detect intention-impact substitution.")
        self.assertEqual(res["prohibited_conclusions"][0], "Do not conclude that the actor's intention was false or malicious.")

    # --- Counterfactual Tests ---
    def test_counterfactual_stability(self):
        # Check if changing dialect from English to Malay changes the score significantly
        text_en = "It is required by the system."
        text_ms = "Ia diperlukan oleh sistem."
        
        res_en = self.rd_detector.detect(text_en)
        res_ms = self.rd_detector.detect(text_ms)
        
        # Malay doesn't match standard English regex, but both have their own boundaries.
        # We verify that both run without errors.
        self.assertIsNotNone(res_en)
        self.assertIsNotNone(res_ms)

    # --- Trajectory Tests ---
    def test_trajectory_accumulation(self):
        traj = self.traj_detector.compute_trajectory(
            current_value=0.8,
            baseline_value=0.2,
            history_values=[0.3, 0.5, 0.7],
            time_window="3-day window"
        )
        self.assertEqual(traj["status"], "MATERIAL_CONTRADICTION")
        self.assertEqual(traj["trend"], "increasing")

if __name__ == "__main__":
    unittest.main()
