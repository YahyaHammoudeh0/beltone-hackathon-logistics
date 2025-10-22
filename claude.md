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

## Notes

- This is a competition/hackathon environment
- Focus on solution quality (cost minimization) and validity
- The environment automatically validates all solutions
- Both dashboard and headless modes use identical validation logic
- Reproducibility is supported via random seeds
