# PLATO Surrogate — Self-Healing Protocol

**Self-healing protocol for PLATO rooms based on the Free Energy Principle (Friston, 2005).**

## Overview

When agents in the Cocapn fleet encounter unexpected outcomes (prediction errors), the Surrogate Protocol kicks in:

1. **Surprise Reported** → Written to `dmn_counterfactuals` room
2. **DMN Generates Counterfactuals** → "What if we had done X instead?"
3. **ECN Evaluates** → Which alternative is most likely to succeed?
4. **Best Path Encoded** → Stored as a tile for future reference

## The Science

**Free Energy Principle (Friston):** Systems resist a tendency toward disorder (entropy). They do this by minimizing "surprise" — the difference between predictions and observations.

In the fleet context:
- Agents form beliefs about expected outcomes
- When reality violates those beliefs, surprise occurs
- The system responds by generating counterfactual paths
- The best counterfactual gets encoded for future action

**DMN (Default Mode Network):** Generates alternative scenarios — mental simulation of "what if." In our implementation, this creates counterfactual tiles.

**ECN (Executive Control Network):** Evaluates alternatives and selects the best action. In our implementation, this encodes winning paths.

## Installation

```bash
pip install plato-surrogate
```

## Usage

```python
from plato_surrogate import SurrogateProtocol

sp = SurrogateProtocol(plato_url="http://localhost:8847")

# Report an unexpected outcome
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
```

## Full Self-Healing Protocol

```python
from plato_surrogate import SurrogateProtocol

sp = SurrogateProtocol()

# One call does it all
result = sp.self_heal(
    agent="kimi-cli",
    event="the refactor broke test coverage",
    expected="all tests pass after refactor",
    observed="coverage dropped from 80% to 52%"
)
```

## API Reference

### `SurrogateProtocol(plato_url="http://localhost:8847")`

Initializes the protocol with a PLATO endpoint.

### `report_surprise(agent, event, expected, observed, domain="fleet_orchestration")`

Reports a prediction error to PLATO's DMN room.

### `generate_counterfactuals(event, num_alternatives=5)`

DMN generates alternative paths. Returns list of counterfactual descriptions.

### `evaluate_and_encode(counterfactuals)`

ECN selects the best alternative and encodes it to the alternatives room.

### `self_heal(agent, event, expected, observed)`

Runs the full pipeline: report → counterfactuals → evaluate → encode.

### `get_alternatives_for(event_keywords)`

Query PLATO for relevant alternatives by keyword.

## Rooms

- `dmn_counterfactuals` — Stores surprise reports and counterfactual tiles
- `ecn_alternatives` — Stores evaluated and encoded best alternatives

## License

MIT