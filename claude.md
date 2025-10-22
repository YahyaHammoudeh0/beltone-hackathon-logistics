# Claude Code Assistant Guide - Beltone Hackathon

## Project Overview

This is a **Beltone Hackathon** project focused on solving the **Multi-Depot Vehicle Routing Problem (MDVRP)** using the Robin Logistics Environment. The goal is to develop an optimized routing algorithm that efficiently delivers orders from multiple warehouses using a fleet of vehicles with different capacities and constraints.

## Problem Domain

### What is MDVRP?
The Multi-Depot Vehicle Routing Problem involves:
- **Multiple warehouses** (depots) with inventory and vehicles
- **Multiple orders** at various delivery locations
- **Fleet of vehicles** with different capacities (weight, volume) and costs
- **Road network** with actual distances between nodes
- **Constraints**: capacity limits, inventory availability, route distance limits

### Optimization Goals
1. Minimize total delivery cost (distance traveled + fixed costs)
2. Fulfill all orders efficiently
3. Respect vehicle capacity constraints
4. Respect inventory availability at warehouses
5. Ensure vehicles return to their home warehouse

## Environment Setup

### Installation
```bash
pip install robin-logistics-env
```

### Project Structure
```
.
├── solver.py                      # Main solver implementation (my_solver function)
├── run_dashboard.py               # Launch interactive Streamlit dashboard
├── README.md                      # User guide and quick start
├── API_REFERENCE.md               # Complete API documentation
├── functions_examples_documentation.xlsx  # Function examples
├── Hackathon Document.docx        # Problem description and rules
├── requirements.txt               # Python dependencies
└── claude.md                      # This file - Claude assistant guide
```

## Key Files to Understand

### solver.py
- **Main entry point**: `my_solver(env)` function
- This is where the routing algorithm should be implemented
- Currently a skeleton - needs implementation
- Should return a solution dict with routes

### run_dashboard.py
- Launches the Streamlit dashboard for visualization
- Connects the solver to the interactive UI
- Useful for testing and debugging routes visually

### API_REFERENCE.md
- Complete documentation of all available functions
- Data models (Warehouse, Vehicle, Order, SKU, Node)
- Environment methods for accessing data
- Essential reading for implementation

## Core Concepts

### Data Models

#### Environment Access
```python
env = LogisticsEnvironment()

# Collections (dicts - access by ID)
env.warehouses     # Dict[str, Warehouse]
env.orders         # Dict[str, Order]
env.skus           # Dict[str, SKU]
env.nodes          # Dict[int, Node]

# Lists (iterate directly)
env.get_all_vehicles()        # List[Vehicle]
env.get_all_order_ids()       # List[str]
env.get_available_vehicles()  # List[str]
```

#### Key Entities

**Warehouse**
- `warehouse.id` - Unique identifier (e.g., "WH-1")
- `warehouse.location` - Node object with lat/lon
- `warehouse.inventory` - Dict[sku_id, quantity]
- `warehouse.vehicles` - List of Vehicle objects

**Vehicle**
- `vehicle.id` - Unique identifier (e.g., "V-1")
- `vehicle.type` - "LightVan", "MediumTruck", "HeavyTruck"
- `vehicle.home_warehouse_id` - Must start and end here
- `vehicle.capacity_weight` - Max weight in kg
- `vehicle.capacity_volume` - Max volume in m³
- `vehicle.max_distance` - Maximum route distance in km
- `vehicle.cost_per_km` - Cost per kilometer
- `vehicle.fixed_cost` - Fixed operational cost

**Order**
- `order.id` - Unique identifier (e.g., "ORD-1")
- `order.destination` - Node object (delivery location)
- `order.requested_items` - Dict[sku_id, quantity]

**SKU**
- `sku.id` - "Light_Item", "Medium_Item", "Heavy_Item"
- `sku.weight` - Weight per unit in kg
- `sku.volume` - Volume per unit in m³

**Node**
- `node.id` - Unique identifier (integer)
- `node.lat`, `node.lon` - Geographic coordinates

### Solution Format

The solver must return a solution dictionary:

```python
solution = {
    "routes": [
        {
            "vehicle_id": "V-1",
            "steps": [
                {
                    "node_id": 1,  # Home warehouse
                    "pickups": [
                        {
                            "warehouse_id": "WH-1",
                            "sku_id": "Light_Item",
                            "quantity": 30
                        }
                    ],
                    "deliveries": [],
                    "unloads": []
                },
                {
                    "node_id": 5,  # Order location
                    "pickups": [],
                    "deliveries": [
                        {
                            "order_id": "ORD-1",
                            "sku_id": "Light_Item",
                            "quantity": 30
                        }
                    ],
                    "unloads": []
                },
                {
                    "node_id": 1,  # Return to home warehouse
                    "pickups": [],
                    "deliveries": [],
                    "unloads": []
                }
            ]
        }
    ]
}
```

### Critical Methods

```python
# Data Access
env.get_warehouse_inventory(warehouse_id)  # Get available inventory
env.get_order_requirements(order_id)       # Get what order needs
env.get_order_location(order_id)           # Get delivery node ID
env.get_vehicle_by_id(vehicle_id)          # Get vehicle details

# Network & Distance
env.get_road_network_data()                # Get adjacency list
env.get_distance(node1_id, node2_id)       # Get distance between nodes
env.get_route_distance(route)              # Calculate total route distance

# Vehicle State
env.get_vehicle_remaining_capacity(vehicle_id)  # (weight, volume) available
env.get_vehicle_current_load(vehicle_id)        # Current cargo

# Validation
env.validate_solution(solution)            # Check if solution is valid
```

## Algorithm Development Strategy

### Recommended Approach

1. **Start Simple**
   - One vehicle, one order first
   - Build valid routes with home warehouse → pickup → delivery → return

2. **Build Pathfinding**
   - Use BFS/Dijkstra on the road network adjacency list
   - Find shortest paths between nodes

3. **Assignment Problem**
   - Which orders to which vehicles?
   - Consider vehicle capacity and warehouse inventory
   - Nearest warehouse heuristic

4. **Route Optimization**
   - Cluster orders by location
   - Consider multiple orders per vehicle
   - Minimize total distance

5. **Advanced Techniques**
   - Genetic algorithms
   - Simulated annealing
   - 2-opt, 3-opt improvements
   - Clarke-Wright savings algorithm

### Common Patterns

```python
# Get road network for pathfinding
road_network = env.get_road_network_data()
adjacency_list = road_network.get("adjacency_list", {})

# BFS pathfinding template
from collections import deque

def find_shortest_path(start_node, end_node, adjacency_list):
    if start_node == end_node:
        return [start_node]

    queue = deque([(start_node, [start_node])])
    visited = {start_node}

    while queue:
        current, path = queue.popleft()

        for neighbor in adjacency_list.get(current, []):
            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor == end_node:
                    return new_path
                visited.add(neighbor)
                queue.append((neighbor, new_path))

    return None

# Check if vehicle can handle order
def can_vehicle_fulfill_order(env, vehicle_id, order_id):
    requirements = env.get_order_requirements(order_id)
    total_weight = sum(
        env.skus[sku_id].weight * qty
        for sku_id, qty in requirements.items()
    )
    total_volume = sum(
        env.skus[sku_id].volume * qty
        for sku_id, qty in requirements.items()
    )

    vehicle = env.get_vehicle_by_id(vehicle_id)
    return (total_weight <= vehicle.capacity_weight and
            total_volume <= vehicle.capacity_volume)
```

## Testing and Debugging

### Dashboard Mode
```bash
python run_dashboard.py
```
- Visual interface to see routes on a map
- Interactive testing of solutions
- Real-time validation feedback

### Headless Mode
```python
env = LogisticsEnvironment()
solution = my_solver(env)
is_valid = env.validate_solution(solution)
metrics = env.get_metrics(solution)
print(f"Valid: {is_valid}")
print(f"Total Cost: {metrics['total_cost']}")
```

### Key Metrics
- **Total Cost**: Sum of all route costs (distance + fixed costs)
- **Total Distance**: Sum of all route distances
- **Delivery Efficiency**: Orders fulfilled vs. total orders
- **Vehicle Utilization**: How well vehicle capacity is used

## Development Workflow

### When Helping with This Project

1. **Read API_REFERENCE.md** first for detailed method documentation
2. **Check existing solution** in solver.py to understand current approach
3. **Test incrementally** - build and validate small parts first
4. **Use dashboard** to visualize and debug routes
5. **Validate often** - use env.validate_solution() to catch errors early

### Common Tasks

**Implementing a new algorithm**
- Modify `my_solver()` function in solver.py
- Keep the function signature: `def my_solver(env) -> Dict`
- Return solution dict in the correct format
- Test with dashboard

**Debugging route issues**
- Check node IDs exist in env.nodes
- Verify inventory availability before pickup
- Ensure vehicles return to home warehouse
- Check capacity constraints aren't violated

**Optimizing performance**
- Profile which parts are slow
- Consider heuristics to reduce search space
- Cache distance calculations
- Use efficient data structures (sets, dicts)

## Tips for Claude Code

- Always reference line numbers when discussing code
- Suggest testing after each change
- Use the dashboard for visual verification
- Break complex algorithms into testable functions
- Consider edge cases (empty orders, insufficient inventory, etc.)
- The environment handles state management - focus on algorithm logic
- Validation is automatic - focus on generating valid solutions

## Resources

- **Package Homepage**: https://github.com/RobinDataScience/Logistics-Env
- **Contact**: mario.salama@beltoneholding.com
- **Package Version**: 3.3.0

## Research-Based Insights (From Academic Papers)

### Key Findings from TSP Research

#### 1. **Computational Efficiency Matters**
From "The Balancing TSP" paper (Madani et al., 2020):
- TSP is **NP-hard** - optimal solutions are computationally expensive
- **Heuristic methods are preferred** over exact algorithms for real-world applications
- **Simulated annealing** showed superiority over many other metaheuristics
- For problems requiring many iterations, heuristics are essential

**Practical Implication**: Don't try to find perfect routes. Use fast, good-enough heuristics.

#### 2. **TSP Tour Length Estimation**
Classical formula (Beardwood et al., 1959):
```
T = b√(N×A)
```
Where:
- T = tour length
- N = number of nodes
- A = area
- b ≈ 0.712-0.765 (constant varies by distance metric)

**Practical Implication**: Estimate if a route is feasible BEFORE building it.

#### 3. **Incremental Distance Growth Pattern**
When adding nodes to existing routes:
```
ΔDistance = coefficient × n^(-power)
```
Where n = number of existing nodes

**Key insight**: As routes get more nodes, each additional node adds LESS incremental distance (saturation effect).

**Practical Implication**: Packing more orders per vehicle is more efficient than expected.

#### 4. **Warehouse Order Picking Patterns**
Classic **Pareto distribution** (from warehouse research):
- 70% of orders come from 10% of items
- 20% of orders from next 20% of items
- 10% of orders from remaining 70% of items

**Practical Implication**: Not all orders are created equal - prioritize high-demand areas.

#### 5. **Distance Metrics**
- **Euclidean distance**: Straight-line, theoretical minimum
- **Manhattan distance**: Grid-based, practical for warehouses/cities
- Road network distances are typically 1.2-1.4× Euclidean distance

**Practical Implication**: Use actual network distances, not Euclidean shortcuts.

### Algorithm Design Principles

#### Multi-Pass Assignment Strategy
From successful implementations:

**Pass 1: Aggressive multi-order packing**
- Try to fit 3-5 orders per vehicle
- Use capacity constraints with safety margin (90-95%)
- Pre-check distance feasibility

**Pass 2: Moderate assignment**
- Handle remaining orders with unused vehicles
- Try 1-2 orders per vehicle

**Pass 3: Last resort**
- Single orders with ANY available vehicle
- Ensures maximum fulfillment

#### Fallback Logic Pattern
```python
for order_batch in [full_list, half_list, single_order]:
    route = try_build_route(order_batch)
    if route:
        accept_and_break()
```

**Why it works**: Routes can fail for many reasons. Trying smaller batches increases success rate.

#### Distance Pre-Checking
Before building expensive routes:
```python
estimated_dist = quick_estimate(orders)
if estimated_dist > vehicle.max_distance * threshold:
    reject_early()  # Don't waste time building this route
```

**Threshold recommendations**:
- Conservative: 70% (fewer failures, lower fulfillment)
- Aggressive: 80-90% (more attempts, better fulfillment)

### Optimization Techniques

#### 1. **Nearest Neighbor Heuristic**
For ordering deliveries within a route:
```python
current = warehouse_node
while unvisited_orders:
    nearest = min(unvisited_orders, key=lambda o: distance(current, o))
    visit(nearest)
    current = nearest.location
```

**Complexity**: O(n²) - fast enough for our problem size

#### 2. **Capacity-Aware Assignment**
Sort orders by size (largest first):
```python
orders.sort(key=lambda o: get_size(o), reverse=True)
```

**Why**: Ensures large orders get vehicles early, smaller orders can fill gaps.

#### 3. **Inventory Validation**
Check warehouse inventory BEFORE building routes:
```python
def has_inventory(warehouse, orders):
    needs = aggregate_requirements(orders)
    inventory = warehouse.inventory
    return all(inventory.get(sku) >= qty for sku, qty in needs.items())
```

**Why**: Avoids wasted pathfinding on impossible routes.

#### 4. **BFS Pathfinding with Limits**
```python
def find_path_bfs(start, end, adj_list, max_nodes=500):
    # Limit exploration to prevent timeout
    nodes_checked = 0
    while queue and nodes_checked < max_nodes:
        nodes_checked += 1
        # ... BFS logic
```

**Why**: Prevents pathfinding from taking too long on impossible paths.

### Performance Patterns

#### What Works (Proven in Research & Our Tests)
✅ Multi-order per vehicle (3-5 orders depending on vehicle type)
✅ Two-pass assignment (aggressive + mop-up)
✅ Fallback from complex → simple routes
✅ Capacity safety margins (90-95% of max)
✅ Distance pre-checking before route building
✅ Nearest neighbor delivery ordering
✅ BFS with node limits for pathfinding

#### What Doesn't Work
❌ Single order per vehicle (poor utilization, low fulfillment)
❌ Too conservative distance checks (<70% threshold)
❌ Ignoring capacity safety margins (causes failures)
❌ Complex route optimization without fallback (fragile)
❌ No node limits on pathfinding (timeouts)

### Constraint Programming Approach
From dp-cp19.pdf paper:

**Decomposition strategy**:
1. **Assignment phase**: Which orders → which vehicles?
2. **Routing phase**: What path for each vehicle?

**Why decompose**: Each subproblem is simpler than joint optimization.

**Branch-and-bound concepts**:
- Prune infeasible branches early
- Use bounds to avoid exploring bad solutions
- Applied in our "distance pre-checking" strategy

### Scoring Strategy for Competition

Given scoring formula:
```
Score = Cost + (Benchmark × (100 - Fulfillment%))
```

**Trade-offs**:
- **Low cost but low fulfillment**: Heavy penalty from benchmark
- **High fulfillment but high cost**: Better - penalty decreases with each order filled
- **Sweet spot**: 80%+ fulfillment with reasonable routing

**Priority**: Fulfillment first, then optimize cost.

### Current Implementation Status

**VibeCoders_solver_1.py** (78% fulfillment, $7,000 cost):
✅ Implements multi-pass assignment
✅ Has fallback logic
✅ Uses capacity checking
✅ BFS pathfinding with limits
✅ Nearest neighbor optimization
⚠️ Room for improvement on last 22% of orders

**Next optimization opportunities**:
1. Adjust distance threshold (try 80-85% instead of 70%)
2. Better warehouse assignment (consider multiple warehouses per vehicle)
3. Order clustering by location before assignment
4. 2-opt local search improvements on routes

## Notes

- This is a competition/hackathon environment
- Focus on solution quality (cost minimization) and validity
- The environment automatically validates all solutions
- Both dashboard and headless modes use identical validation logic
- Reproducibility is supported via random seeds