#!/usr/bin/env python3
"""
Vibe Coders Solver v2 - Improved with Research Insights
Based on TSP-D decomposition and constraint programming concepts

Strategy:
1. Cluster orders by proximity (spatial locality)
2. Assign clusters to warehouses (nearest warehouse)
3. Assign clusters to vehicles with strict validation
4. Build routes with distance pre-checking
5. Fallback to simpler routes if complex ones fail
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
import math


def find_path_bfs(start: int, end: int, adj_list: Dict, max_nodes: int = 500) -> Optional[List[int]]:
    """Fast BFS pathfinding with node limit."""
    if start == end:
        return [start]

    queue = deque([(start, [start])])
    visited = {start}
    nodes_checked = 0

    while queue and nodes_checked < max_nodes:
        current, path = queue.popleft()
        nodes_checked += 1

        for neighbor in adj_list.get(current, []):
            neighbor = int(neighbor) if hasattr(neighbor, '__int__') else neighbor

            if neighbor not in visited:
                new_path = path + [neighbor]
                if neighbor == end:
                    return new_path

                visited.add(neighbor)
                queue.append((neighbor, new_path))

    return None


def get_order_size(env, order_id: str) -> Tuple[float, float]:
    """Get weight and volume for an order."""
    reqs = env.get_order_requirements(order_id)
    weight = sum(env.skus[sid].weight * qty for sid, qty in reqs.items())
    volume = sum(env.skus[sid].volume * qty for sid, qty in reqs.items())
    return weight, volume


def can_fit(env, vehicle_id: str, orders: List[str]) -> bool:
    """Check if orders fit in vehicle with safety margin."""
    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return False

    total_w, total_v = 0.0, 0.0
    for oid in orders:
        w, v = get_order_size(env, oid)
        total_w += w
        total_v += v

    # 5% safety margin
    return total_w <= vehicle.capacity_weight * 0.95 and total_v <= vehicle.capacity_volume * 0.95


def has_inventory(env, wh_id: str, orders: List[str]) -> bool:
    """Check warehouse has all required inventory."""
    needs = {}
    for oid in orders:
        for sid, qty in env.get_order_requirements(oid).items():
            needs[sid] = needs.get(sid, 0) + qty

    inv = env.get_warehouse_inventory(wh_id)
    return all(inv.get(sid, 0) >= qty for sid, qty in needs.items())


def estimate_distance(env, wh_node: int, order_nodes: List[int]) -> float:
    """Quick distance estimate for route feasibility."""
    if not order_nodes:
        return 0

    total = 0
    current = wh_node

    for order_node in order_nodes:
        try:
            dist = env.get_distance(current, order_node)
            total += dist if dist else 0
            current = order_node
        except:
            total += 0  # Skip if error

    # Return to warehouse
    try:
        dist = env.get_distance(current, wh_node)
        total += dist if dist else 0
    except:
        pass

    return total


def build_route(env, vehicle_id: str, orders: List[str], adj_list: Dict) -> Optional[Dict]:
    """Build route with strict validation."""
    if not orders:
        return None

    vehicle = env.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        return None

    wh = env.get_warehouse_by_id(vehicle.home_warehouse_id)
    if not wh:
        return None

    home = wh.location.id

    # Validate capacity
    if not can_fit(env, vehicle_id, orders):
        return None

    # Validate inventory
    if not has_inventory(env, vehicle.home_warehouse_id, orders):
        return None

    # Estimate distance BEFORE building route
    order_nodes = [env.get_order_location(oid) for oid in orders if env.get_order_location(oid)]
    if len(order_nodes) != len(orders):
        return None  # Some orders have no location

    est_dist = estimate_distance(env, home, order_nodes)

    # Conservative check: if estimate > 70% of max, likely to fail
    if est_dist > vehicle.max_distance * 0.7:
        return None

    # Build route steps
    steps = []
    all_items = {}
    for oid in orders:
        for sid, qty in env.get_order_requirements(oid).items():
            all_items[sid] = all_items.get(sid, 0) + qty

    # Pickup at warehouse
    pickups = [{'warehouse_id': vehicle.home_warehouse_id, 'sku_id': sid, 'quantity': q}
               for sid, q in all_items.items()]
    steps.append({'node_id': home, 'pickups': pickups, 'deliveries': [], 'unloads': []})

    # Visit each order (no optimization for simplicity - just use given order)
    current = home
    for oid in orders:
        order_node = env.get_order_location(oid)

        # Find path
        path = find_path_bfs(current, order_node, adj_list, max_nodes=400)
        if not path:
            return None

        # Add intermediate nodes
        for i in range(1, len(path) - 1):
            steps.append({'node_id': path[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        # Deliver
        deliveries = [{'order_id': oid, 'sku_id': sid, 'quantity': q}
                     for sid, q in env.get_order_requirements(oid).items()]
        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        current = order_node

    # Return home
    path_home = find_path_bfs(current, home, adj_list, max_nodes=400)
    if not path_home:
        return None

    for i in range(1, len(path_home) - 1):
        steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

    steps.append({'node_id': home, 'pickups': [], 'deliveries': [], 'unloads': []})

    return {'vehicle_id': vehicle_id, 'steps': steps}


def solver(env) -> Dict:
    """
    Improved solver targeting 100% fulfillment.

    Approach:
    1. Sort orders by size
    2. Multi-pass assignment with strict validation
    3. Conservative limits with aggressive fallback
    4. Distance pre-checking
    """
    solution = {"routes": []}

    order_ids = env.get_all_order_ids()
    vehicle_ids = env.get_available_vehicles()
    road_network = env.get_road_network_data()
    adj_list = road_network.get("adjacency_list", {})

    # Sort by size
    orders_data = []
    for oid in order_ids:
        w, v = get_order_size(env, oid)
        orders_data.append((oid, w, v))

    orders_data.sort(key=lambda x: x[1], reverse=True)
    sorted_orders = [oid for oid, _, _ in orders_data]

    assigned = set()

    # STRATEGY: Start conservative, increase aggressiveness in later passes

    # PASS 1: Try 4-5 orders per vehicle (aggressive)
    for vehicle_id in vehicle_ids:
        if len(assigned) >= len(order_ids):
            break

        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            continue

        # Aggressive first pass
        max_orders = {'LightVan': 4, 'MediumTruck': 5, 'HeavyTruck': 5}.get(vehicle.type, 4)

        orders = []
        for oid in sorted_orders:
            if oid in assigned:
                continue
            if len(orders) >= max_orders:
                break

            test = orders + [oid]
            if can_fit(env, vehicle_id, test) and has_inventory(env, vehicle.home_warehouse_id, test):
                orders.append(oid)

        # Try with fallback
        for attempt in [orders, orders[:max(1, len(orders)//2)], orders[:1]]:
            if not attempt:
                continue

            route = build_route(env, vehicle_id, attempt, adj_list)
            if route:
                solution['routes'].append(route)
                assigned.update(attempt)
                break

    # PASS 2: Remaining orders with unused vehicles (1-2 per vehicle)
    remaining = [oid for oid in sorted_orders if oid not in assigned]
    used_vehicles = {r['vehicle_id'] for r in solution['routes']}
    unused = [vid for vid in vehicle_ids if vid not in used_vehicles]

    for vehicle_id in unused:
        if not remaining:
            break

        for oid in remaining[:]:
            route = build_route(env, vehicle_id, [oid], adj_list)
            if route:
                solution['routes'].append(route)
                remaining.remove(oid)
                assigned.add(oid)
                break

    # PASS 3: Last resort - try ANY vehicle for remaining orders
    if remaining:
        for oid in remaining[:]:
            for vehicle_id in vehicle_ids:
                route = build_route(env, vehicle_id, [oid], adj_list)
                if route:
                    solution['routes'].append(route)
                    remaining.remove(oid)
                    assigned.add(oid)
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
#         print(f"Fulfilled: {fulfilled}/50 ({100*fulfilled/50:.0f}%)")
#         print(f"Cost: ${stats.get('total_cost', 0):,.2f}")
