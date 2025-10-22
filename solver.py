#!/usr/bin/env python3

#pip install robin-logistics-env  --- Before first run install in the terminal
"""
Contestant solver for the Robin Logistics Environment.

Generates a valid solution using basic assignment and BFS-based routing.
"""
from robin_logistics import LogisticsEnvironment
from typing import Dict, List, Optional, Tuple, Set
from collections import deque


def find_shortest_path(start_node: int, end_node: int, adjacency_list: Dict) -> Optional[List[int]]:
    """
    Find shortest path between two nodes using BFS.

    Args:
        start_node: Starting node ID
        end_node: Destination node ID
        adjacency_list: Road network adjacency list

    Returns:
        List of node IDs representing the path, or None if no path exists
    """
    if start_node == end_node:
        return [start_node]

    queue = deque([(start_node, [start_node])])
    visited = {start_node}

    while queue:
        current, path = queue.popleft()

        # Limit path length to avoid infinite loops
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
    """
    Calculate total weight and volume required for an order.

    Args:
        env: LogisticsEnvironment instance
        order_id: Order identifier

    Returns:
        Tuple of (total_weight, total_volume)
    """
    requirements = env.get_order_requirements(order_id)
    total_weight = 0.0
    total_volume = 0.0

    for sku_id, quantity in requirements.items():
        sku = env.skus[sku_id]
        total_weight += sku.weight * quantity
        total_volume += sku.volume * quantity

    return total_weight, total_volume


def can_vehicle_handle_order(env, vehicle_id: str, order_id: str) -> bool:
    """
    Check if a vehicle can handle an order based on capacity.

    Args:
        env: LogisticsEnvironment instance
        vehicle_id: Vehicle identifier
        order_id: Order identifier

    Returns:
        True if vehicle can handle the order, False otherwise
    """
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    order_weight, order_volume = calculate_order_weight_volume(env, order_id)

    return (order_weight <= vehicle.capacity_weight and
            order_volume <= vehicle.capacity_volume)


def warehouse_has_inventory(env, warehouse_id: str, order_id: str) -> bool:
    """
    Check if warehouse has sufficient inventory for an order.

    Args:
        env: LogisticsEnvironment instance
        warehouse_id: Warehouse identifier
        order_id: Order identifier

    Returns:
        True if warehouse has sufficient inventory, False otherwise
    """
    requirements = env.get_order_requirements(order_id)
    inventory = env.get_warehouse_inventory(warehouse_id)

    for sku_id, quantity in requirements.items():
        if inventory.get(sku_id, 0) < quantity:
            return False

    return True


def create_route_for_order(env, vehicle_id: str, order_id: str, adjacency_list: Dict) -> Optional[Dict]:
    """
    Create a complete route for a vehicle to deliver one order.

    Args:
        env: LogisticsEnvironment instance
        vehicle_id: Vehicle identifier
        order_id: Order identifier
        adjacency_list: Road network adjacency list

    Returns:
        Route dictionary or None if route cannot be created
    """
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    # Check capacity
    if not can_vehicle_handle_order(env, vehicle_id, order_id):
        return None

    # Get warehouse and check inventory
    home_warehouse_id = vehicle.home_warehouse_id
    home_warehouse = env.get_warehouse_by_id(home_warehouse_id)
    if not home_warehouse:
        return None

    if not warehouse_has_inventory(env, home_warehouse_id, order_id):
        return None

    # Get order location
    order_location = env.get_order_location(order_id)
    if order_location is None:
        return None

    home_node = home_warehouse.location.id

    # Build the route steps
    steps = []

    # Step 1: Start at warehouse and pickup items
    requirements = env.get_order_requirements(order_id)
    warehouse_pickups = []
    for sku_id, quantity in requirements.items():
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

    # Step 2: Travel to order location (add intermediate nodes)
    path_to_order = find_shortest_path(home_node, order_location, adjacency_list)
    if not path_to_order or len(path_to_order) < 2:
        return None

    # Add intermediate nodes (excluding start and end)
    for i in range(1, len(path_to_order) - 1):
        steps.append({
            'node_id': path_to_order[i],
            'pickups': [],
            'deliveries': [],
            'unloads': []
        })

    # Step 3: Deliver at order location
    order_deliveries = []
    for sku_id, quantity in requirements.items():
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

    # Step 4: Return to warehouse (add intermediate nodes)
    path_to_home = find_shortest_path(order_location, home_node, adjacency_list)
    if not path_to_home or len(path_to_home) < 2:
        return None

    # Add intermediate nodes (excluding start and end)
    for i in range(1, len(path_to_home) - 1):
        steps.append({
            'node_id': path_to_home[i],
            'pickups': [],
            'deliveries': [],
            'unloads': []
        })

    # Step 5: End at warehouse
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
    Greedy solver: Assign each order to the first available vehicle that can handle it.

    Strategy:
    1. Sort orders by size (weight) - handle larger orders first
    2. For each order, find a vehicle that can handle it
    3. Prefer vehicles from the closest warehouse
    4. Create a simple route: warehouse -> order -> warehouse

    Args:
        env: LogisticsEnvironment instance

    Returns:
        A complete solution dict with routes and sequential steps.
    """
    solution = {"routes": []}

    # Get all data
    order_ids: List[str] = env.get_all_order_ids()
    available_vehicle_ids: List[str] = env.get_available_vehicles()
    road_network = env.get_road_network_data()
    adjacency_list = road_network.get("adjacency_list", {})

    # Track which vehicles have been used
    used_vehicles: Set[str] = set()
    fulfilled_orders: Set[str] = set()

    # Sort orders by size (larger orders first to ensure they get vehicles)
    orders_with_size = []
    for order_id in order_ids:
        weight, volume = calculate_order_weight_volume(env, order_id)
        orders_with_size.append((order_id, weight, volume))

    # Sort by weight descending
    orders_with_size.sort(key=lambda x: x[1], reverse=True)
    sorted_order_ids = [order_id for order_id, _, _ in orders_with_size]

    print(f"Processing {len(sorted_order_ids)} orders with {len(available_vehicle_ids)} vehicles...")

    # Greedy assignment: one order per vehicle
    for order_id in sorted_order_ids:
        if order_id in fulfilled_orders:
            continue

        route_created = False

        # Try to find a suitable vehicle
        for vehicle_id in available_vehicle_ids:
            if vehicle_id in used_vehicles:
                continue

            # Try to create a route
            route = create_route_for_order(env, vehicle_id, order_id, adjacency_list)

            if route:
                solution['routes'].append(route)
                used_vehicles.add(vehicle_id)
                fulfilled_orders.add(order_id)
                route_created = True
                print(f"✓ Order {order_id} assigned to {vehicle_id}")
                break

        if not route_created:
            print(f"✗ Could not assign order {order_id}")

    print(f"\nSolution complete: {len(solution['routes'])} routes created")
    print(f"Orders fulfilled: {len(fulfilled_orders)}/{len(order_ids)}")

    return solution


if __name__ == '__main__':
    env = LogisticsEnvironment()
    result = my_solver(env)
    print("\n" + "="*50)
    print("Testing solution validity...")

    # Validate the solution
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
        print(f"  Orders Fulfilled: {statistics.get('orders_fulfilled', 0)}/{statistics.get('total_orders', 0)}")
 
