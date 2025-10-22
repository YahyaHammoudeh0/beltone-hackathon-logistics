#!/usr/bin/env python3
"""
Vibe Coders - Final Submission: 100% Fulfillment Target
Improved multi-order routing with robust error handling
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque


def find_shortest_path(start_node: int, end_node: int, adjacency_list: Dict, max_nodes: int = 500) -> Optional[List[int]]:
    """BFS pathfinding with node limit."""
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
    """Calculate weight and volume."""
    requirements = env.get_order_requirements(order_id)
    total_weight = 0.0
    total_volume = 0.0

    for sku_id, quantity in requirements.items():
        sku = env.skus[sku_id]
        total_weight += sku.weight * quantity
        total_volume += sku.volume * quantity

    return total_weight, total_volume


def can_fit_orders(env, vehicle_id: str, order_ids: List[str]) -> bool:
    """Check capacity with safety margin."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    total_weight = 0.0
    total_volume = 0.0

    for order_id in order_ids:
        weight, volume = calculate_order_size(env, order_id)
        total_weight += weight
        total_volume += volume

    # 10% safety margin
    return (total_weight <= vehicle.capacity_weight * 0.9 and
            total_volume <= vehicle.capacity_volume * 0.9)


def check_inventory(env, warehouse_id: str, order_ids: List[str]) -> bool:
    """Verify inventory availability."""
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


def optimize_delivery_sequence(env, warehouse_node: int, order_ids: List[str]) -> List[str]:
    """Order deliveries using nearest neighbor."""
    if len(order_ids) <= 1:
        return order_ids

    unvisited = set(order_ids)
    route = []
    current = warehouse_node

    while unvisited:
        nearest = None
        min_dist = float('inf')

        for oid in unvisited:
            order_node = env.get_order_location(oid)
            try:
                dist = env.get_distance(current, order_node) or float('inf')
                if dist < min_dist:
                    min_dist = dist
                    nearest = oid
            except:
                pass

        if nearest:
            route.append(nearest)
            unvisited.remove(nearest)
            current = env.get_order_location(nearest)
        else:
            # Fallback: add remaining in original order
            route.extend(list(unvisited))
            break

    return route


def estimate_route_distance(env, warehouse_node: int, order_nodes: List[int]) -> float:
    """Estimate total route distance."""
    if not order_nodes:
        return 0

    total = 0
    current = warehouse_node

    # To each order
    for order_node in order_nodes:
        try:
            dist = env.get_distance(current, order_node)
            total += dist if dist else 50  # Assume 50km if unknown
            current = order_node
        except:
            total += 50

    # Back to warehouse
    try:
        dist = env.get_distance(current, warehouse_node)
        total += dist if dist else 50
    except:
        total += 50

    return total


def create_route(env, vehicle_id: str, order_ids: List[str], adjacency_list: Dict) -> Optional[Dict]:
    """Create multi-order route with distance checking."""
    if not order_ids:
        return None

    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
    if not warehouse:
        return None

    home_node = warehouse.location.id

    # Check capacity
    if not can_fit_orders(env, vehicle_id, order_ids):
        return None

    # Check inventory
    if not check_inventory(env, vehicle.home_warehouse_id, order_ids):
        return None

    # Optimize order sequence
    optimized_orders = optimize_delivery_sequence(env, home_node, order_ids)

    # Estimate distance before creating route
    order_nodes = [env.get_order_location(oid) for oid in optimized_orders]
    estimated_distance = estimate_route_distance(env, home_node, order_nodes)

    # Check against vehicle max distance (with 20% buffer for actual vs estimated)
    if estimated_distance > vehicle.max_distance * 0.8:
        return None

    # Build route
    steps = []
    all_items = {}
    for order_id in order_ids:
        requirements = env.get_order_requirements(order_id)
        for sku_id, qty in requirements.items():
            all_items[sku_id] = all_items.get(sku_id, 0) + qty

    # Pickup at warehouse
    pickups = [{'warehouse_id': vehicle.home_warehouse_id, 'sku_id': sid, 'quantity': q}
               for sid, q in all_items.items()]
    steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

    # Visit each order
    current_node = home_node
    for order_id in optimized_orders:
        order_node = env.get_order_location(order_id)
        if order_node is None:
            return None

        # Path to order
        path = find_shortest_path(current_node, order_node, adjacency_list, max_nodes=500)
        if not path:
            return None

        # Add intermediate nodes
        for i in range(1, len(path) - 1):
            steps.append({'node_id': path[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        # Deliver
        requirements = env.get_order_requirements(order_id)
        deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                     for sid, q in requirements.items()]
        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        current_node = order_node

    # Return home
    path_home = find_shortest_path(current_node, home_node, adjacency_list, max_nodes=500)
    if not path_home:
        return None

    for i in range(1, len(path_home) - 1):
        steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

    steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

    return {'vehicle_id': vehicle_id, 'steps': steps}


def solver(env) -> Dict:
    """
    Robust multi-order solver with fallback logic.

    Strategy:
    1. Try to assign multiple orders per vehicle
    2. If route creation fails, try with fewer orders
    3. Use conservative limits based on vehicle type
    4. Prioritize fulfillment over cost optimization
    """
    solution = {"routes": []}

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

    # Process each vehicle
    for vehicle_id in vehicle_ids:
        if len(assigned) >= len(order_ids):
            break

        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            continue

        # Max orders based on vehicle type - conservative
        max_orders = {'LightVan': 3, 'MediumTruck': 4, 'HeavyTruck': 5}.get(vehicle.type, 3)

        # Try to pack orders
        vehicle_orders = []
        for order_id in sorted_orders:
            if order_id in assigned:
                continue

            if len(vehicle_orders) >= max_orders:
                break

            test_orders = vehicle_orders + [order_id]
            if can_fit_orders(env, vehicle_id, test_orders):
                if check_inventory(env, vehicle.home_warehouse_id, test_orders):
                    vehicle_orders.append(order_id)

        # Try to create route with fallback
        route = None
        attempts = [vehicle_orders, vehicle_orders[:len(vehicle_orders)//2], vehicle_orders[:1]]

        for attempt_orders in attempts:
            if not attempt_orders:
                continue

            route = create_route(env, vehicle_id, attempt_orders, adjacency_list)
            if route:
                solution['routes'].append(route)
                assigned.update(attempt_orders)
                break

    return solution


# # COMMENT OUT WHEN SUBMITTING
# if __name__ == '__main__':
#     from robin_logistics import LogisticsEnvironment
#     env = LogisticsEnvironment()
#     result = solver(env)
#
#     is_valid, msg, details = env.validate_solution_complete(result)
#     print(f"Valid: {is_valid}")
#
#     if is_valid:
#         success, exec_msg = env.execute_solution(result)
#         print(f"Execution: {exec_msg}")
#
#         fulfilled = sum(1 for oid in env.get_all_order_ids()
#                        if all(qty == 0 for qty in env.get_order_fulfillment_status(oid).get('remaining', {}).values()))
#
#         stats = env.get_solution_statistics(result, details)
#         print(f"Fulfilled: {fulfilled}/50")
#         print(f"Cost: ${stats.get('total_cost', 0):,.2f}")
