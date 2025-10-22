#!/usr/bin/env python3
"""
Vibe Coders - Beltone AI Hackathon Submission v5
Ultra-Conservative Single-Order Solver

Design philosophy: MAXIMUM SIMPLICITY = MAXIMUM RELIABILITY

Response to persistent failures in scenarios 3 & 4:
- V3: 0%, 11% failures
- V4: 0%, 11% failures (same scenarios!)
- V5: Ultra-simple single-order only approach

Strategy:
- ONE order per route (most reliable)
- Increased BFS limit: 2000 nodes
- Try EVERY vehicle for EVERY order
- Smallest orders first (easier to place)
- Zero complexity, maximum robustness

Target: 0% failure rate, accept lower avg fulfillment if needed
"""
from typing import Dict, List, Optional, Tuple
from collections import deque


# ============================================================================
# ULTRA-ROBUST PATHFINDING
# ============================================================================

def find_path_ultra_robust(start_node: int, end_node: int, adjacency_list: Dict, max_length: int = 2000) -> Optional[List[int]]:
    """
    Ultra-robust BFS with 2000-node limit and extensive error handling.
    """
    if start_node is None or end_node is None:
        return None

    if start_node == end_node:
        return [start_node]

    try:
        queue = deque([(start_node, [start_node])])
        visited = {start_node}
        nodes_explored = 0

        while queue and nodes_explored < max_length * 2:
            nodes_explored += 1
            current, path = queue.popleft()

            if len(path) >= max_length:
                continue

            neighbors = adjacency_list.get(current, [])

            for neighbor in neighbors:
                try:
                    neighbor_int = int(neighbor) if hasattr(neighbor, '__int__') else neighbor

                    if neighbor_int is None:
                        continue

                    if neighbor_int not in visited:
                        new_path = path + [neighbor_int]

                        if neighbor_int == end_node:
                            return new_path

                        visited.add(neighbor_int)
                        queue.append((neighbor_int, new_path))
                except:
                    continue

        return None
    except:
        return None


def calculate_order_size_safe(env, order_id: str) -> Tuple[float, float]:
    """Calculate order size with error handling."""
    try:
        requirements = env.get_order_requirements(order_id)
        total_weight = 0.0
        total_volume = 0.0

        for sku_id, quantity in requirements.items():
            sku = env.skus.get(sku_id)
            if sku:
                total_weight += sku.weight * quantity
                total_volume += sku.volume * quantity

        return total_weight, total_volume
    except:
        return 0.0, 0.0


def can_vehicle_carry_order(env, vehicle_id: str, order_id: str) -> bool:
    """Check if vehicle can carry order with 90% safety margin."""
    try:
        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return False

        weight, volume = calculate_order_size_safe(env, order_id)

        # 90% safety margin for reliability
        return (weight <= vehicle.capacity_weight * 0.9 and
                volume <= vehicle.capacity_volume * 0.9)
    except:
        return False


def warehouse_has_inventory(env, warehouse_id: str, order_id: str) -> bool:
    """Check if warehouse has inventory for order."""
    try:
        requirements = env.get_order_requirements(order_id)
        inventory = env.get_warehouse_inventory(warehouse_id)

        for sku_id, qty in requirements.items():
            if inventory.get(sku_id, 0) < qty:
                return False

        return True
    except:
        return False


# ============================================================================
# SINGLE-ORDER ROUTE CREATION
# ============================================================================

def create_ultra_simple_route(env, vehicle_id: str, order_id: str, adjacency_list: Dict) -> Optional[Dict]:
    """
    Create the simplest possible route: ONE vehicle, ONE order.

    This is the most reliable approach possible.
    """
    try:
        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return None

        warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
        if not warehouse:
            return None

        home_node = warehouse.location.id
        if home_node is None:
            return None

        # Check capacity
        if not can_vehicle_carry_order(env, vehicle_id, order_id):
            return None

        # Check inventory
        if not warehouse_has_inventory(env, warehouse.id, order_id):
            return None

        # Get order location
        order_node = env.get_order_location(order_id)
        if order_node is None:
            return None

        # Find path to order (2000-node limit)
        path_to_order = find_path_ultra_robust(home_node, order_node, adjacency_list, max_length=2000)
        if not path_to_order:
            return None

        # Find path back home
        path_home = find_path_ultra_robust(order_node, home_node, adjacency_list, max_length=2000)
        if not path_home:
            return None

        # Build simple route
        requirements = env.get_order_requirements(order_id)
        pickups = [{'warehouse_id': warehouse.id, 'sku_id': sid, 'quantity': q}
                   for sid, q in requirements.items()]
        deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                      for sid, q in requirements.items()]

        steps = []

        # Step 1: Start at warehouse, pickup
        steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

        # Steps 2-N: Travel to order
        for i in range(1, len(path_to_order) - 1):
            steps.append({'node_id': path_to_order[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        # Deliver
        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        # Return home
        for i in range(1, len(path_home) - 1):
            steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

        return {'vehicle_id': vehicle_id, 'steps': steps}

    except Exception as e:
        return None


# ============================================================================
# ULTRA-SIMPLE SOLVER
# ============================================================================

def solver(env) -> Dict:
    """
    Ultra-conservative solver: ONE order per vehicle, try everything.

    Strategy:
    1. Sort orders by size (smallest first - easier to place)
    2. For each order, try EVERY vehicle until one works
    3. Use 2000-node BFS limit for difficult scenarios
    4. Accept lower average fulfillment for zero failure rate

    This is the simplest, most reliable approach possible.
    No multi-order complexity, no optimization, just reliability.
    """
    solution = {"routes": []}

    try:
        # Get data
        order_ids = env.get_all_order_ids()
        vehicle_ids = env.get_available_vehicles()
        adjacency_list = env.get_road_network_data().get("adjacency_list", {})

        if not order_ids or not vehicle_ids:
            return solution

        # Sort orders by size (SMALLEST first - easier to fit)
        orders_with_size = []
        for oid in order_ids:
            weight, volume = calculate_order_size_safe(env, oid)
            orders_with_size.append((oid, weight, volume))

        orders_with_size.sort(key=lambda x: x[1])  # Smallest first
        sorted_orders = [oid for oid, _, _ in orders_with_size]

        # Track used vehicles
        used_vehicles = set()

        # Strategy: Try to assign each order to any available vehicle
        for order_id in sorted_orders:
            # Try each vehicle
            for vehicle_id in vehicle_ids:
                if vehicle_id in used_vehicles:
                    continue

                # Try to create route
                route = create_ultra_simple_route(env, vehicle_id, order_id, adjacency_list)

                if route:
                    solution['routes'].append(route)
                    used_vehicles.add(vehicle_id)
                    break  # Found a vehicle for this order, move to next order

        return solution

    except Exception as e:
        # Ultimate fallback
        return {"routes": []}


# # COMMENT OUT THIS SECTION WHEN SUBMITTING
# if __name__ == '__main__':
#     from robin_logistics import LogisticsEnvironment
#     env = LogisticsEnvironment()
#     result = solver(env)
#
#     print(f"Routes created: {len(result['routes'])}")
#
#     # Validate
#     is_valid, msg, details = env.validate_solution_complete(result)
#     print(f"Valid: {is_valid}")
#     print(f"Message: {msg}")
#
#     if is_valid:
#         stats = env.get_solution_statistics(result, details)
#         fulfillment = env.get_solution_fulfillment_summary(result, details)
#         print(f"Cost: ${stats.get('total_cost', 0):,.2f}")
#         print(f"Distance: {stats.get('total_distance', 0):,.2f} km")
#         print(f"Fulfillment: {fulfillment.get('fully_fulfilled_orders', 0)}/{len(env.get_all_order_ids())}")
