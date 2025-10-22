#!/usr/bin/env python3
"""
Vibe Coders - Beltone AI Hackathon Submission
Multi-Depot Vehicle Routing Problem Solver

Strategy: Greedy multi-order assignment with capacity-aware routing
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque


def find_shortest_path(start_node: int, end_node: int, adjacency_list: Dict, max_length: int = 500) -> Optional[List[int]]:
    """BFS shortest path finding."""
    if start_node == end_node:
        return [start_node]

    queue = deque([(start_node, [start_node])])
    visited = {start_node}

    while queue:
        current, path = queue.popleft()

        if len(path) >= max_length:
            continue

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
    """Calculate total weight and volume for an order."""
    requirements = env.get_order_requirements(order_id)
    total_weight = 0.0
    total_volume = 0.0

    for sku_id, quantity in requirements.items():
        sku = env.skus[sku_id]
        total_weight += sku.weight * quantity
        total_volume += sku.volume * quantity

    return total_weight, total_volume


def can_fit_orders(env, vehicle_id: str, order_ids: List[str]) -> bool:
    """Check if orders fit in vehicle capacity."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    total_weight = 0.0
    total_volume = 0.0

    for order_id in order_ids:
        weight, volume = calculate_order_size(env, order_id)
        total_weight += weight
        total_volume += volume

    return (total_weight <= vehicle.capacity_weight and
            total_volume <= vehicle.capacity_volume)


def check_warehouse_inventory(env, warehouse_id: str, order_ids: List[str]) -> bool:
    """Check if warehouse has inventory for all orders."""
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


def optimize_delivery_order(env, warehouse_node: int, order_ids: List[str]) -> List[str]:
    """Optimize order sequence using nearest neighbor."""
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
            route.extend(list(unvisited))
            break

    return route


def create_route(env, vehicle_id: str, order_ids: List[str], adjacency_list: Dict) -> Optional[Dict]:
    """Create multi-order route for a vehicle."""
    if not order_ids:
        return None

    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
    if not warehouse:
        return None

    home_node = warehouse.location.id

    # Collect all required items
    all_items = {}
    for order_id in order_ids:
        requirements = env.get_order_requirements(order_id)
        for sku_id, qty in requirements.items():
            all_items[sku_id] = all_items.get(sku_id, 0) + qty

    # Check inventory
    if not check_warehouse_inventory(env, vehicle.home_warehouse_id, order_ids):
        return None

    # Optimize order sequence
    optimized_orders = optimize_delivery_order(env, home_node, order_ids)

    steps = []

    # Step 1: Pickup at warehouse
    pickups = [{'warehouse_id': vehicle.home_warehouse_id, 'sku_id': sid, 'quantity': q}
               for sid, q in all_items.items()]
    steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

    # Steps 2-N: Visit each order
    current_node = home_node
    for order_id in optimized_orders:
        order_node = env.get_order_location(order_id)
        if order_node is None:
            return None

        # Path to order
        path = find_shortest_path(current_node, order_node, adjacency_list)
        if not path:
            return None

        # Add intermediate nodes
        for i in range(1, len(path) - 1):
            steps.append({'node_id': path[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        # Deliver all SKUs for this order at once
        requirements = env.get_order_requirements(order_id)
        deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                     for sid, q in requirements.items()]
        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        current_node = order_node

    # Return home
    path_home = find_shortest_path(current_node, home_node, adjacency_list)
    if not path_home:
        return None

    for i in range(1, len(path_home) - 1):
        steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

    steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

    return {'vehicle_id': vehicle_id, 'steps': steps}


def solver(env) -> Dict:
    """
    Main solver function - assigns multiple orders per vehicle.

    Strategy:
    1. Sort orders by size (largest first)
    2. For each vehicle, pack as many orders as capacity allows
    3. Optimize delivery sequence
    4. Generate valid routes
    """
    solution = {"routes": []}

    # Get data
    order_ids = env.get_all_order_ids()
    vehicle_ids = env.get_available_vehicles()
    road_network = env.get_road_network_data()
    adjacency_list = road_network.get("adjacency_list", {})

    # Sort orders by size (largest first to ensure they get vehicles)
    orders_with_size = []
    for oid in order_ids:
        weight, volume = calculate_order_size(env, oid)
        orders_with_size.append((oid, weight, volume))

    orders_with_size.sort(key=lambda x: x[1], reverse=True)
    sorted_orders = [oid for oid, _, _ in orders_with_size]

    # Track assignments
    assigned = set()

    # Assign orders to vehicles
    for vehicle_id in vehicle_ids:
        if len(assigned) >= len(order_ids):
            break

        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            continue

        # Limit orders per vehicle based on type to ensure route reliability
        # Conservative limits to avoid route execution failures
        max_orders_per_vehicle = {
            'LightVan': 3,
            'MediumTruck': 4,
            'HeavyTruck': 5
        }.get(vehicle.type, 3)

        vehicle_orders = []

        # Try to add orders to this vehicle
        for order_id in sorted_orders:
            if order_id in assigned:
                continue

            if len(vehicle_orders) >= max_orders_per_vehicle:
                break

            # Check if order fits
            test_orders = vehicle_orders + [order_id]
            if not can_fit_orders(env, vehicle_id, test_orders):
                continue

            # Check inventory
            if not check_warehouse_inventory(env, vehicle.home_warehouse_id, test_orders):
                continue

            vehicle_orders.append(order_id)

        # Create route if orders assigned
        if vehicle_orders:
            route = create_route(env, vehicle_id, vehicle_orders, adjacency_list)
            if route:
                solution['routes'].append(route)
                assigned.update(vehicle_orders)

    return solution


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
#         print(f"Cost: ${stats.get('total_cost', 0):,.2f}")
#         print(f"Distance: {stats.get('total_distance', 0):,.2f} km")
