#!/usr/bin/env python3

"""
Improved solver that allows multiple orders per vehicle.

This version uses a greedy bin-packing approach:
1. Group orders by proximity (clustering)
2. Assign multiple orders to each vehicle based on capacity
3. Optimize route order using nearest neighbor
"""
from robin_logistics import LogisticsEnvironment
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
import math


def find_shortest_path(start_node: int, end_node: int, adjacency_list: Dict) -> Optional[List[int]]:
    """Find shortest path between two nodes using BFS."""
    if start_node == end_node:
        return [start_node]

    queue = deque([(start_node, [start_node])])
    visited = {start_node}

    while queue:
        current, path = queue.popleft()

        if len(path) > 500:
            continue

        neighbors = adjacency_list.get(current, [])
        for neighbor in neighbors:
            neighbor_int = int(neighbor) if hasattr(neighbor, '__int__') else neighbor

            if neighbor_int not in visited:
                new_path = path + [neighbor_int]

                if neighbor_int == end_node:
                    return new_path

                visited.add(neighbor_int)
                queue.append((neighbor_int, new_path))

    return None


def calculate_order_weight_volume(env, order_id: str) -> Tuple[float, float]:
    """Calculate total weight and volume for an order."""
    requirements = env.get_order_requirements(order_id)
    total_weight = 0.0
    total_volume = 0.0

    for sku_id, quantity in requirements.items():
        sku = env.skus[sku_id]
        total_weight += sku.weight * quantity
        total_volume += sku.volume * quantity

    return total_weight, total_volume


def get_distance(env, node1: int, node2: int) -> float:
    """Get distance between two nodes."""
    try:
        dist = env.get_distance(node1, node2)
        return dist if dist is not None else float('inf')
    except:
        return float('inf')


def can_add_order_to_vehicle(env, vehicle_id: str, current_orders: List[str], new_order_id: str) -> bool:
    """Check if adding an order to a vehicle's route would exceed capacity."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    # Calculate total weight and volume for all orders
    total_weight = 0.0
    total_volume = 0.0

    for order_id in current_orders + [new_order_id]:
        weight, volume = calculate_order_weight_volume(env, order_id)
        total_weight += weight
        total_volume += volume

    return (total_weight <= vehicle.capacity_weight and
            total_volume <= vehicle.capacity_volume)


def optimize_order_sequence(env, warehouse_node: int, order_ids: List[str]) -> List[str]:
    """
    Order visits using nearest neighbor heuristic.

    Args:
        env: Environment
        warehouse_node: Starting warehouse node
        order_ids: List of orders to visit

    Returns:
        Optimized order sequence
    """
    if not order_ids:
        return []

    if len(order_ids) == 1:
        return order_ids

    # Nearest neighbor heuristic
    unvisited = set(order_ids)
    route = []
    current_node = warehouse_node

    while unvisited:
        nearest_order = None
        nearest_dist = float('inf')

        for order_id in unvisited:
            order_node = env.get_order_location(order_id)
            dist = get_distance(env, current_node, order_node)

            if dist < nearest_dist:
                nearest_dist = dist
                nearest_order = order_id

        if nearest_order:
            route.append(nearest_order)
            unvisited.remove(nearest_order)
            current_node = env.get_order_location(nearest_order)

    return route


def create_multi_order_route(env, vehicle_id: str, order_ids: List[str], adjacency_list: Dict) -> Optional[Dict]:
    """
    Create a route for a vehicle to deliver multiple orders.

    Args:
        env: LogisticsEnvironment
        vehicle_id: Vehicle ID
        order_ids: List of order IDs to deliver
        adjacency_list: Road network

    Returns:
        Route dictionary or None
    """
    if not order_ids:
        return None

    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    home_warehouse_id = vehicle.home_warehouse_id
    home_warehouse = env.get_warehouse_by_id(home_warehouse_id)
    if not home_warehouse:
        return None

    home_node = home_warehouse.location.id

    # Check inventory for all orders
    all_requirements = {}
    for order_id in order_ids:
        requirements = env.get_order_requirements(order_id)
        for sku_id, qty in requirements.items():
            all_requirements[sku_id] = all_requirements.get(sku_id, 0) + qty

    # Check warehouse has sufficient inventory
    inventory = env.get_warehouse_inventory(home_warehouse_id)
    for sku_id, qty in all_requirements.items():
        if inventory.get(sku_id, 0) < qty:
            return None

    # Optimize order sequence
    optimized_orders = optimize_order_sequence(env, home_node, order_ids)

    steps = []

    # Step 1: Pickup all items at warehouse
    warehouse_pickups = []
    for sku_id, quantity in all_requirements.items():
        warehouse_pickups.append({
            'warehouse_id': home_warehouse_id,
            'sku_id': sku_id,
            'quantity': quantity
        })

    steps.append({
        'node_id': home_node,
        'pickups': warehouse_pickups,
        'deliveries': [],
        'unloads': []
    })

    # Step 2-N: Visit each order location in optimized sequence
    current_node = home_node

    for order_id in optimized_orders:
        order_location = env.get_order_location(order_id)
        if order_location is None:
            return None

        # Find path to order
        path_to_order = find_shortest_path(current_node, order_location, adjacency_list)
        if not path_to_order:
            return None

        # Add intermediate nodes
        for i in range(1, len(path_to_order) - 1):
            steps.append({
                'node_id': path_to_order[i],
                'pickups': [],
                'deliveries': [],
                'unloads': []
            })

        # Deliver at order location
        order_requirements = env.get_order_requirements(order_id)
        order_deliveries = []
        for sku_id, quantity in order_requirements.items():
            order_deliveries.append({
                'order_id': order_id,
                'sku_id': sku_id,
                'quantity': quantity
            })

        steps.append({
            'node_id': order_location,
            'pickups': [],
            'deliveries': order_deliveries,
            'unloads': []
        })

        current_node = order_location

    # Return to warehouse
    path_home = find_shortest_path(current_node, home_node, adjacency_list)
    if not path_home:
        return None

    for i in range(1, len(path_home) - 1):
        steps.append({
            'node_id': path_home[i],
            'pickups': [],
            'deliveries': [],
            'unloads': []
        })

    steps.append({
        'node_id': home_node,
        'pickups': [],
        'deliveries': [],
        'unloads': []
    })

    return {
        'vehicle_id': vehicle_id,
        'steps': steps
    }


def my_solver(env) -> Dict:
    """
    Improved greedy solver that assigns multiple orders per vehicle.

    Strategy:
    1. Sort orders by size (larger first)
    2. For each vehicle, pack as many orders as capacity allows
    3. Optimize delivery sequence using nearest neighbor
    4. Continue until all orders assigned or vehicles exhausted

    Args:
        env: LogisticsEnvironment instance

    Returns:
        Complete solution dictionary
    """
    solution = {"routes": []}

    # Get data
    order_ids: List[str] = env.get_all_order_ids()
    available_vehicle_ids: List[str] = env.get_available_vehicles()
    road_network = env.get_road_network_data()
    adjacency_list = road_network.get("adjacency_list", {})

    # Track assignment
    assigned_orders: Set[str] = set()
    used_vehicles: Set[str] = set()

    # Sort orders by size (weight descending)
    orders_with_size = []
    for order_id in order_ids:
        weight, volume = calculate_order_weight_volume(env, order_id)
        orders_with_size.append((order_id, weight, volume))

    orders_with_size.sort(key=lambda x: x[1], reverse=True)
    sorted_order_ids = [order_id for order_id, _, _ in orders_with_size]

    print(f"Processing {len(sorted_order_ids)} orders with {len(available_vehicle_ids)} vehicles...")
    print("Using multi-order per vehicle strategy...\n")

    # Try to assign orders to vehicles
    for vehicle_id in available_vehicle_ids:
        if len(assigned_orders) >= len(order_ids):
            break

        vehicle_orders = []

        # Try to add orders to this vehicle
        for order_id in sorted_order_ids:
            if order_id in assigned_orders:
                continue

            # Check if we can add this order
            if can_add_order_to_vehicle(env, vehicle_id, vehicle_orders, order_id):
                # Check warehouse inventory
                vehicle = env.get_vehicle_by_id(vehicle_id)
                warehouse_id = vehicle.home_warehouse_id

                # Calculate requirements for this batch
                test_requirements = {}
                for test_order_id in vehicle_orders + [order_id]:
                    req = env.get_order_requirements(test_order_id)
                    for sku_id, qty in req.items():
                        test_requirements[sku_id] = test_requirements.get(sku_id, 0) + qty

                # Check inventory
                inventory = env.get_warehouse_inventory(warehouse_id)
                has_inventory = all(
                    inventory.get(sku_id, 0) >= qty
                    for sku_id, qty in test_requirements.items()
                )

                if has_inventory:
                    vehicle_orders.append(order_id)

        # If we assigned any orders to this vehicle, create a route
        if vehicle_orders:
            route = create_multi_order_route(env, vehicle_id, vehicle_orders, adjacency_list)

            if route:
                solution['routes'].append(route)
                for order_id in vehicle_orders:
                    assigned_orders.add(order_id)
                used_vehicles.add(vehicle_id)

                print(f"✓ Vehicle {vehicle_id}: {len(vehicle_orders)} orders - {vehicle_orders}")

    print(f"\n{'='*60}")
    print(f"Solution complete:")
    print(f"  Routes created: {len(solution['routes'])}")
    print(f"  Vehicles used: {len(used_vehicles)}/{len(available_vehicle_ids)}")
    print(f"  Orders fulfilled: {len(assigned_orders)}/{len(order_ids)}")
    print(f"  Fulfillment rate: {100 * len(assigned_orders) / len(order_ids):.1f}%")

    return solution


if __name__ == '__main__':
    env = LogisticsEnvironment()
    result = my_solver(env)
    print("\n" + "="*60)
    print("Testing solution validity...")

    # Validate
    is_valid, validation_message, validation_details = env.validate_solution_complete(result)
    print(f"Solution valid: {is_valid}")
    print(f"Message: {validation_message}")

    if is_valid:
        # Get statistics
        statistics = env.get_solution_statistics(result, validation_details)
        print(f"\nMetrics:")
        print(f"  Total Cost: ${statistics.get('total_cost', 0):,.2f}")
        print(f"  Total Distance: {statistics.get('total_distance', 0):,.2f} km")
        print(f"  Vehicles Used: {len(result['routes'])}")
