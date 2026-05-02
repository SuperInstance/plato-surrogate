"""
PLATO Surrogate — Self-Healing Protocol for PLATO

Based on Free Energy Principle (Friston):
- The fleet acts to minimize surprise
- When an agent encounters unexpected outcomes (high surprise), it writes to PLATO
- DMN generates counterfactual paths ("what if we had done X instead?")
- ECN evaluates and the best alternative gets encoded

This is the Self-Healing Protocol:
- Failure creates prediction error → written to PLATO
- DMN generates alternative histories → written as tiles
- ECN evaluates which alternatives are most likely to succeed
- Best alternative encoded as new tile for future agents to reference

Usage:
    from plato_surrogate import SurrogateProtocol
    sp = SurrogateProtocol(plato_url="http://localhost:8847")

    # Agent reports unexpected outcome
    sp.report_surprise(
        agent="kimi-cli",
        event="the refactor broke test coverage",
        expected="all tests pass after refactor",
        observed="coverage dropped from 80% to 52%"
    )

    # DMN generates counterfactuals
    counterfactuals = sp.generate_counterfactuals("test coverage drop during refactor")

    # ECN evaluates and picks the best alternative
    verdict = sp.evaluate_and_encode(counterfactuals)
    print(verdict)  # {"alternative": "...", "efficacy": 0.78}
"""

import requests
import time
from typing import List, Dict, Any, Optional


class SurrogateProtocol:
    def __init__(self, plato_url: str = "http://localhost:8847"):
        self.plato_url = plato_url.rstrip("/")
        self.dmn_room = "dmn_counterfactuals"
        self.ecn_room = "ecn_alternatives"

    def report_surprise(
        self,
        agent: str,
        event: str,
        expected: str,
        observed: str,
        domain: str = "fleet_orchestration"
    ) -> Dict[str, Any]:
        """
        Report an unexpected outcome (surprise) to PLATO.

        This is the entry point for the self-healing protocol.
        """
        surprise_tile = {
            "question": f"What surprised {agent}?",
            "answer": f"Agent: {agent}\nExpected: {expected}\nObserved: {observed}\nEvent: {event}",
            "agent": agent,
            "domain": domain,
            "confidence": 0.95,  # High confidence in the failure report
            "model": agent,
            "role": "surprise_report",
            "surprise_type": "prediction_error"
        }

        try:
            resp = requests.post(f"{self.plato_url}/room/{self.dmn_room}", json=surprise_tile, timeout=5)
            return {"status": "written", "surprise_id": f"{agent}_{int(time.time())}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_counterfactuals(self, event: str, num_alternatives: int = 5) -> List[str]:
        """
        DMN generates counterfactual paths.

        In the real implementation, this would call Seed-2.0-mini via DeepInfra.
        For now, generates structured counterfactual tiles.

        Counterfactuals ask: "What if we had done X instead?"
        """
        counterfactual_templates = [
            f"What if we had NOT done the refactor that caused: {event}?",
            f"What if we had done incremental refactoring instead of big-bang for: {event}?",
            f"What if we had added tests BEFORE refactoring for: {event}?",
            f"What if we had rolled back the refactor immediately after noticing: {event}?",
            f"What if we had used a feature flag to isolate the change causing: {event}?",
        ]

        results = []
        for cf in counterfactual_templates[:num_alternatives]:
            tile = {
                "question": f"Counterfactual: {cf}",
                "answer": f"Alternative path: {cf}\nHypothetical outcome would be different from: {event}",
                "agent": "dmn_surrogate",
                "domain": "dmn_counterfactuals",
                "confidence": 0.7,
                "model": "seed-2.0-mini",
                "role": "counterfactual_generator"
            }
            try:
                requests.post(f"{self.plato_url}/room/{self.dmn_room}", json=tile, timeout=5)
                results.append(cf)
            except:
                pass

        return results

    def evaluate_and_encode(self, counterfactuals: List[str]) -> Dict[str, Any]:
        """
        ECN evaluates counterfactuals and encodes the best one.

        In the real implementation, this would call DeepSeek-v4-flash.
        For now, picks the first counterfactual as the 'best' and encodes it.
        """
        if not counterfactuals:
            return {"status": "no_alternatives", "alternative": None, "efficacy": 0.0}

        best = counterfactuals[0]  # In reality: DeepSeek scores these

        encoded_tile = {
            "question": f"What alternative should we use next time?",
            "answer": f"Best alternative: {best}\nReason: This path avoids the surprise event.\nEncoded for future reference.",
            "agent": "ecn_surrogate",
            "domain": "ecn_alternatives",
            "confidence": 0.82,
            "model": "deepseek-v4-flash",
            "role": "ecn_encoder"
        }

        try:
            requests.post(f"{self.plato_url}/room/{self.ecn_room}", json=encoded_tile, timeout=5)
            return {"status": "encoded", "alternative": best, "efficacy": 0.82}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def self_heal(self, agent: str, event: str, expected: str, observed: str) -> Dict[str, Any]:
        """
        Full self-healing protocol: report → counterfactuals → evaluate → encode.
        """
        # Step 1: Report the surprise
        report = self.report_surprise(agent, event, expected, observed)

        # Step 2: Generate counterfactual alternatives
        counterfactuals = self.generate_counterfactuals(event)

        # Step 3: ECN evaluates and encodes the best alternative
        verdict = self.evaluate_and_encode(counterfactuals)

        return {
            "surprise_reported": report,
            "counterfactuals_generated": len(counterfactuals),
            "best_alternative_encoded": verdict
        }

    def get_alternatives_for(self, event_keywords: str) -> List[Dict[str, Any]]:
        """Query PLATO for alternatives that address similar events."""
        try:
            resp = requests.get(f"{self.plato_url}/room/{self.ecn_room}?limit=50", timeout=5)
            if resp.status_code == 200:
                tiles = resp.json().get("tiles", [])
                relevant = [
                    t for t in tiles
                    if event_keywords.lower() in str(t.get("answer", "")).lower()
                ]
                return relevant
        except:
            pass
        return []