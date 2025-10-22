#!/usr/bin/env python3
"""
Vibe Coders - Improved Solver for 100% Fulfillment
Focus: Reliability over optimization
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque


def find_shortest_path(start_node: int, end_node: int, adjacency_list: Dict, max_nodes: int = 300) -> Optional[List[int]]:
    """BFS with stricter node limit for reliability."""
    if start_node == end_node:
        return [start_node]

    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    nodes_explored = 0

    while queue and nodes_explored < max_nodes:
        current, path = queue.popleft()
        nodes_explored += 1

        for neighbor in adjacency_list.get(current, []):
            neighbor_int = int(neighbor) if hasattr(neighbor, '__int__') else neighbor

            if neighbor_int not in visited:
                new_path = path + [neighbor_int]

                if neighbor_int == end_node:
                    return new_path

                visited.add(neighbor_int)
                queue.append((neighbor_int, new_path))

    return None


def calculate_order_size(env, order_id: str) -> Tuple[float, float]:
    """Calculate weight and volume for an order."""
    requirements = env.get_order_requirements(order_id)
    total_weight = 0.0
    total_volume = 0.0

    for sku_id, quantity in requirements.items():
        sku = env.skus[sku_id]
        total_weight += sku.weight * quantity
        total_volume += sku.volume * quantity

    return total_weight, total_volume


def can_fit_orders(env, vehicle_id: str, order_ids: List[str]) -> bool:
    """Check capacity constraints."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    total_weight = 0.0
    total_volume = 0.0

    for order_id in order_ids:
        weight, volume = calculate_order_size(env, order_id)
        total_weight += weight
        total_volume += volume

    return (total_weight <= vehicle.capacity_weight * 0.95 and  # 5% safety margin
            total_volume <= vehicle.capacity_volume * 0.95)


def check_inventory(env, warehouse_id: str, order_ids: List[str]) -> bool:
    """Verify warehouse has inventory."""
    total_needs = {}
    for order_id in order_ids:
        requirements = env.get_order_requirements(order_id)
        for sku_id, qty in requirements.items():
            total_needs[sku_id] = total_needs.get(sku_id, 0) + qty

    inventory = env.get_warehouse_inventory(warehouse_id)
    for sku_id, qty in total_needs.items():
        if inventory.get(sku_id, 0) < qty:
            return False

    return True


def create_single_order_route(env, vehicle_id: str, order_id: str, adjacency_list: Dict) -> Optional[Dict]:
    """Create simple route for ONE order - maximum reliability."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
    if not warehouse:
        return None

    # Check capacity
    if not can_fit_orders(env, vehicle_id, [order_id]):
        return None

    # Check inventory
    if not check_inventory(env, vehicle.home_warehouse_id, [order_id]):
        return None

    home_node = warehouse.location.id
    order_node = env.get_order_location(order_id)
    if order_node is None:
        return None

    # Find path with strict limit
    path_to_order = find_shortest_path(home_node, order_node, adjacency_list, max_nodes=300)
    if not path_to_order:
        return None

    path_home = find_shortest_path(order_node, home_node, adjacency_list, max_nodes=300)
    if not path_home:
        return None

    # Build steps
    steps = []
    requirements = env.get_order_requirements(order_id)

    # Pickup at warehouse
    pickups = [{'warehouse_id': vehicle.home_warehouse_id, 'sku_id': sid, 'quantity': q}
               for sid, q in requirements.items()]
    steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

    # Travel to order (intermediate nodes)
    for i in range(1, len(path_to_order) - 1):
        steps.append({'node_id': path_to_order[i], 'pickups': [], 'deliveries': [], 'unloads': []})

    # Deliver
    deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                 for sid, q in requirements.items()]
    steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

    # Return home (intermediate nodes)
    for i in range(1, len(path_home) - 1):
        steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

    steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

    return {'vehicle_id': vehicle_id, 'steps': steps}


def solver(env) -> Dict:
    """
    Ultra-reliable solver: ONE order per vehicle for guaranteed execution.

    Strategy: Simplicity over complexity
    - Assign exactly 1 order per vehicle
    - Use shortest, simplest paths
    - Maximize reliability
    """
    solution = {"routes": []}

    # Get data
    order_ids = env.get_all_order_ids()
    vehicle_ids = env.get_available_vehicles()
    road_network = env.get_road_network_data()
    adjacency_list = road_network.get("adjacency_list", {})

    # Sort orders by size
    orders_with_size = []
    for oid in order_ids:
        weight, volume = calculate_order_size(env, oid)
        orders_with_size.append((oid, weight, volume))

    orders_with_size.sort(key=lambda x: x[1], reverse=True)
    sorted_orders = [oid for oid, _, _ in orders_with_size]

    assigned = set()

    # Simple assignment: 1 order per vehicle
    for vehicle_id in vehicle_ids:
        if len(assigned) >= len(order_ids):
            break

        # Find first unassigned order that fits
        for order_id in sorted_orders:
            if order_id in assigned:
                continue

            # Try to create route
            route = create_single_order_route(env, vehicle_id, order_id, adjacency_list)

            if route:
                solution['routes'].append(route)
                assigned.add(order_id)
                break

    return solution


# # COMMENT OUT WHEN SUBMITTING
# if __name__ == '__main__':
#     from robin_logistics import LogisticsEnvironment
#     env = LogisticsEnvironment()
#     result = solver(env)
#
#     print(f"Routes: {len(result['routes'])}")
#
#     # Validate and execute
#     is_valid, msg, details = env.validate_solution_complete(result)
#     print(f"Valid: {is_valid}")
#
#     if is_valid:
#         success, exec_msg = env.execute_solution(result)
#         print(f"Execution: {exec_msg}")
#
#         # Check fulfillment
#         fulfilled = sum(1 for oid in env.get_all_order_ids()
#                        if all(qty == 0 for qty in env.get_order_fulfillment_status(oid).get('remaining', {}).values()))
#
#         stats = env.get_solution_statistics(result, details)
#         print(f"\nFulfilled: {fulfilled}/50 ({100*fulfilled/50:.0f}%)")
#         print(f"Cost: ${stats.get('total_cost', 0):,.2f}")
