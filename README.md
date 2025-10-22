# Beltone Hackathon - MDVRP Solver

**Team: Vibe Coders**
Multi-Depot Vehicle Routing Problem solver for Beltone AI Hackathon

## 📊 Current Performance

**Submission File:** `VibeCoders_solver_1.py`

- ✅ **Fulfillment:** 78-88% (39-44 out of 50 orders)
- ✅ **Cost:** ~$7,000
- ✅ **Distance:** 240-290 km
- ✅ **Reliability:** 100% validation success, 92-100% execution

## 🚀 Quick Start

### Installation

```bash
pip install robin-logistics-env
```

### Test Solver

```bash
python test_solver.py
```

### Run Dashboard (Visualization)

```bash
python run_dashboard.py
```

Interactive Streamlit dashboard with:
- Road network and order visualization
- Route testing and validation
- Real-time performance metrics

## 📁 Project Structure

```
.
├── VibeCoders_solver_1.py     # 🏆 Main submission solver (78-88% fulfillment)
├── test_solver.py              # Test script for validation
├── run_dashboard.py            # Interactive visualization dashboard
├── solver.py                   # Original skeleton/template
│
├── README.md                   # This file
├── API_REFERENCE.md            # Complete API documentation
├── claude.md                   # Development guide with research insights
├── requirements.txt            # Python dependencies
│
├── studies/                    # Research papers
│   ├── dp-cp19.pdf
│   └── Thebalancingtravelingsalesmanproblem_Submission.pdf
│
└── Hackathon Document.docx     # Competition rules and requirements
```

## 🎯 Algorithm Overview

**Strategy:** Multi-order greedy assignment with capacity-aware routing

**Key Features:**
1. **BFS Pathfinding** - Shortest path on road network
2. **Multi-order Packing** - 3-5 orders per vehicle based on type
3. **Two-pass Assignment** - Primary + mop-up passes
4. **Three-level Fallback** - Full list → Half → Single order
5. **Capacity & Inventory Validation** - Strict constraint checking
6. **Nearest Neighbor Optimization** - Delivery sequence optimization

## 📈 Submission

**Portal:** https://beltone-ai-hackathon.com/
**Team:** Vibe Coders
**File:** `VibeCoders_solver_1.py`

### Scoring Formula
```
Score = Cost + (Benchmark × (100 - Fulfillment%))
```

**Strategy:** Maximize fulfillment first, then minimize cost.

## 🔬 Research Insights

This solver incorporates insights from academic TSP research:

- **Heuristic over Optimal:** Fast approximations beat expensive exact solutions
- **Fallback Logic:** Try multiple configurations to maximize success rate
- **Capacity Safety:** Conservative margins prevent route failures
- **Nearest Neighbor:** O(n²) routing optimization

**Key Learning:** Simple "try-and-fail" approaches empirically outperform complex pre-filtering strategies in this constrained environment.

See `claude.md` for detailed research analysis and development notes.

## 📚 Documentation

- **API_REFERENCE.md** - Complete environment API
- **claude.md** - Research insights and development guide
- **Hackathon Document.docx** - Competition rules

## 🛠️ Development

### Running Tests

```python
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

env = LogisticsEnvironment()
result = solver(env)

# Validate
is_valid, msg, details = env.validate_solution_complete(result)
print(f"Valid: {is_valid}")

# Execute
success, exec_msg = env.execute_solution(result)
print(f"Execution: {exec_msg}")

# Get stats
stats = env.get_solution_statistics(result, details)
print(f"Cost: ${stats['total_cost']:,.2f}")
```

### Key Environment Methods

```python
# Data access
env.get_all_order_ids()
env.get_available_vehicles()
env.get_warehouse_inventory(warehouse_id)
env.get_order_requirements(order_id)

# Network & distance
env.get_road_network_data()
env.get_distance(node1, node2)

# Validation
env.validate_solution_complete(solution)
env.execute_solution(solution)
env.get_solution_statistics(solution, details)
```

## 📞 Contact

**Package:** https://github.com/RobinDataScience/Logistics-Env
**Contact:** mario.salama@beltoneholding.com
**Version:** 3.3.0

## 📄 License

Beltone AI Hackathon 2024
