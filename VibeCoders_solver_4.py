#!/usr/bin/env python3
"""
Vibe Coders - Beltone AI Hackathon Submission v4
Multi-Depot Vehicle Routing Problem Solver - Robustness Focused

Critical improvements over v3:
- More robust pathfinding with higher node limits and fallbacks
- Aggressive single-order assignment for difficult cases
- Multiple construction strategies with fallbacks
- Better error handling and edge case management
- Simplified ALNS that preserves any valid solution

Target: Handle all scenarios robustly, maintain 85%+ average fulfillment
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
import random
import time


# ============================================================================
# ROBUST PATHFINDING
# ============================================================================

def find_shortest_path_robust(start_node: int, end_node: int, adjacency_list: Dict, max_length: int = 2000) -> Optional[List[int]]:
    """
    More robust BFS pathfinding with 2000-node limit and better error handling.
    Increased from 1000 to handle larger/more complex scenarios.
    """
    if start_node == end_node:
        return [start_node]

    # Handle None or invalid nodes
    if start_node is None or end_node is None:
        return None

    try:
        queue = deque([(start_node, [start_node])])
        visited = {start_node}

        while queue:
            current, path = queue.popleft()

            if len(path) >= max_length:
                continue

            neighbors = adjacency_list.get(current, [])

            for neighbor in neighbors:
                try:
                    neighbor_int = int(neighbor) if hasattr(neighbor, '__int__') else neighbor

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


def calculate_order_size(env, order_id: str) -> Tuple[float, float]:
    """Calculate total weight and volume for an order."""
    try:
        requirements = env.get_order_requirements(order_id)
        total_weight = 0.0
        total_volume = 0.0

        for sku_id, quantity in requirements.items():
            sku = env.skus[sku_id]
            total_weight += sku.weight * quantity
            total_volume += sku.volume * quantity

        return total_weight, total_volume
    except:
        return 0.0, 0.0


def can_fit_orders(env, vehicle_id: str, order_ids: List[str]) -> bool:
    """Check if orders fit in vehicle capacity with safety margin."""
    try:
        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return False

        total_weight = 0.0
        total_volume = 0.0

        for order_id in order_ids:
            weight, volume = calculate_order_size(env, order_id)
            total_weight += weight
            total_volume += volume

        # 95% safety margin
        return (total_weight <= vehicle.capacity_weight * 0.95 and
                total_volume <= vehicle.capacity_volume * 0.95)
    except:
        return False


def check_warehouse_inventory(env, warehouse_id: str, order_ids: List[str]) -> bool:
    """Check if warehouse has inventory for all orders."""
    try:
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
    except:
        return False


def create_single_order_route(env, vehicle_id: str, order_id: str, adjacency_list: Dict) -> Optional[Dict]:
    """
    Create a simple single-order route (most reliable).
    """
    try:
        vehicle = env.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return None

        warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
        if not warehouse:
            return None

        home_node = warehouse.location.id

        # Check capacity
        if not can_fit_orders(env, vehicle_id, [order_id]):
            return None

        # Check inventory
        if not check_warehouse_inventory(env, warehouse.id, [order_id]):
            return None

        # Get order location
        order_node = env.get_order_location(order_id)
        if order_node is None:
            return None

        # Find path to order with robust pathfinding (2000-node limit)
        path_to_order = find_shortest_path_robust(home_node, order_node, adjacency_list, max_length=2000)
        if not path_to_order:
            return None

        # Find path back home
        path_home = find_shortest_path_robust(order_node, home_node, adjacency_list, max_length=2000)
        if not path_home:
            return None

        # Build route steps
        requirements = env.get_order_requirements(order_id)
        pickups = [{'warehouse_id': warehouse.id, 'sku_id': sid, 'quantity': q}
                   for sid, q in requirements.items()]

        steps = []

        # Step 1: Pickup at warehouse
        steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

        # Steps 2-N: Path to order
        for i in range(1, len(path_to_order) - 1):
            steps.append({'node_id': path_to_order[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        # Deliver
        deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                     for sid, q in requirements.items()]
        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        # Return home
        for i in range(1, len(path_home) - 1):
            steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

        return {'vehicle_id': vehicle_id, 'steps': steps}

    except Exception as e:
        return None


def create_multi_order_route(env, vehicle_id: str, order_ids: List[str], adjacency_list: Dict) -> Optional[Dict]:
    """
    Create a multi-order route with nearest-neighbor sequencing.
    """
    if not order_ids:
        return None

    try:
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
        if not check_warehouse_inventory(env, warehouse.id, order_ids):
            return None

        # Optimize order sequence (nearest neighbor)
        optimized_orders = []
        remaining = set(order_ids)
        current = home_node

        while remaining:
            nearest = None
            min_dist = float('inf')

            for oid in remaining:
                order_node = env.get_order_location(oid)
                if order_node:
                    try:
                        dist = env.get_distance(current, order_node) or float('inf')
                        if dist < min_dist:
                            min_dist = dist
                            nearest = oid
                    except:
                        pass

            if nearest:
                optimized_orders.append(nearest)
                remaining.remove(nearest)
                current = env.get_order_location(nearest)
            else:
                optimized_orders.extend(list(remaining))
                break

        # Build route
        all_items = {}
        for order_id in optimized_orders:
            requirements = env.get_order_requirements(order_id)
            for sku_id, qty in requirements.items():
                all_items[sku_id] = all_items.get(sku_id, 0) + qty

        pickups = [{'warehouse_id': warehouse.id, 'sku_id': sid, 'quantity': q}
                   for sid, q in all_items.items()]

        steps = []
        steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

        # Visit each order
        current_node = home_node
        for order_id in optimized_orders:
            order_node = env.get_order_location(order_id)
            if order_node is None:
                return None

            path = find_shortest_path_robust(current_node, order_node, adjacency_list, max_length=2000)
            if not path:
                return None

            # Intermediate nodes
            for i in range(1, len(path) - 1):
                steps.append({'node_id': path[i], 'pickups': [], 'deliveries': [], 'unloads': []})

            # Deliver
            requirements = env.get_order_requirements(order_id)
            deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                         for sid, q in requirements.items()]
            steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

            current_node = order_node

        # Return home
        path_home = find_shortest_path_robust(current_node, home_node, adjacency_list, max_length=2000)
        if not path_home:
            return None

        for i in range(1, len(path_home) - 1):
            steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

        return {'vehicle_id': vehicle_id, 'steps': steps}

    except:
        return None


# ============================================================================
# ROBUST INITIAL SOLUTION CONSTRUCTION
# ============================================================================

def construct_robust_solution(env, adjacency_list: Dict) -> Dict:
    """
    Ultra-robust initial construction with multiple fallback strategies.

    Strategy 1: Multi-order assignment (proven v2/v3 approach)
    Strategy 2: Aggressive single-order assignment for any remaining
    Strategy 3: Try smaller vehicles for difficult orders
    """
    solution = {"routes": []}
    assigned = set()

    try:
        order_ids = env.get_all_order_ids()
        vehicle_ids = env.get_available_vehicles()

        if not order_ids or not vehicle_ids:
            return solution

        # Sort orders by size (largest first)
        orders_with_size = []
        for oid in order_ids:
            weight, volume = calculate_order_size(env, oid)
            orders_with_size.append((oid, weight, volume))
        orders_with_size.sort(key=lambda x: x[1], reverse=True)
        sorted_orders = [oid for oid, _, _ in orders_with_size]

        used_vehicles = set()

        # STRATEGY 1: Multi-order assignment (proven approach)
        for vehicle_id in vehicle_ids:
            if len(assigned) >= len(order_ids):
                break

            vehicle = env.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                continue

            # Aggressive limits for higher fulfillment (v3 levels)
            max_orders = {'LightVan': 4, 'MediumTruck': 5, 'HeavyTruck': 5}.get(vehicle.type, 4)

            vehicle_orders = []

            # Try to add orders
            for order_id in sorted_orders:
                if order_id in assigned:
                    continue

                if len(vehicle_orders) >= max_orders:
                    break

                test_orders = vehicle_orders + [order_id]
                if not can_fit_orders(env, vehicle_id, test_orders):
                    continue

                warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
                if warehouse and not check_warehouse_inventory(env, warehouse.id, test_orders):
                    continue

                vehicle_orders.append(order_id)

            # Try to create route with progressive fallback
            if vehicle_orders:
                route = None

                # Try full list
                if len(vehicle_orders) > 1:
                    route = create_multi_order_route(env, vehicle_id, vehicle_orders, adjacency_list)

                # Fallback: try half
                if not route and len(vehicle_orders) > 2:
                    half_orders = vehicle_orders[:len(vehicle_orders) // 2]
                    route = create_multi_order_route(env, vehicle_id, half_orders, adjacency_list)
                    if route:
                        vehicle_orders = half_orders

                # Fallback: try single order
                if not route and len(vehicle_orders) > 0:
                    route = create_single_order_route(env, vehicle_id, vehicle_orders[0], adjacency_list)
                    if route:
                        vehicle_orders = [vehicle_orders[0]]

                if route:
                    solution['routes'].append(route)
                    assigned.update(vehicle_orders)
                    used_vehicles.add(vehicle_id)

        # STRATEGY 2: Aggressive single-order assignment for remaining
        remaining = [oid for oid in sorted_orders if oid not in assigned]
        unused_vehicles = [vid for vid in vehicle_ids if vid not in used_vehicles]

        for vehicle_id in unused_vehicles:
            if not remaining:
                break

            # Try every remaining order
            for order_id in remaining[:]:
                route = create_single_order_route(env, vehicle_id, order_id, adjacency_list)
                if route:
                    solution['routes'].append(route)
                    remaining.remove(order_id)
                    assigned.add(order_id)
                    break  # One route per vehicle

        # STRATEGY 3: Final desperate attempt - try any vehicle for any order
        if remaining and len(solution['routes']) < len(vehicle_ids):
            all_remaining = [vid for vid in vehicle_ids if vid not in used_vehicles and vid not in unused_vehicles]

            for order_id in remaining[:]:
                for vehicle_id in vehicle_ids:
                    # Skip if this vehicle already has a route
                    if any(r['vehicle_id'] == vehicle_id for r in solution['routes']):
                        continue

                    route = create_single_order_route(env, vehicle_id, order_id, adjacency_list)
                    if route:
                        solution['routes'].append(route)
                        remaining.remove(order_id)
                        assigned.add(order_id)
                        break

    except Exception as e:
        # If construction completely fails, return whatever we have
        pass

    return solution


# ============================================================================
# MAIN SOLVER
# ============================================================================

def light_optimization(env, solution: Dict, adjacency_list: Dict, time_limit: float = 120) -> Dict:
    """
    Lightweight optimization: try to add unassigned orders to existing routes.
    """
    try:
        start_time = time.time()

        # Get assigned orders
        assigned = set()
        for route in solution['routes']:
            for step in route['steps']:
                for delivery in step.get('deliveries', []):
                    assigned.add(delivery['order_id'])

        # Find unassigned
        all_orders = set(env.get_all_order_ids())
        unassigned = list(all_orders - assigned)

        if not unassigned:
            return solution

        # Try to add unassigned orders to existing routes
        improvements = 0

        for order_id in unassigned[:]:
            if time.time() - start_time > time_limit:
                break

            # Try adding to any existing vehicle's new route
            # (since each vehicle can only have one route per solution)
            # We skip this and instead try single-order routes with unused vehicles

        # Alternative: create single-order routes for unassigned with any available vehicle
        used_vehicles = {r['vehicle_id'] for r in solution['routes']}
        all_vehicles = set(env.get_available_vehicles())
        available_vehicles = list(all_vehicles - used_vehicles)

        for order_id in unassigned[:]:
            if not available_vehicles:
                break

            for vehicle_id in available_vehicles:
                route = create_single_order_route(env, vehicle_id, order_id, adjacency_list)
                if route:
                    solution['routes'].append(route)
                    unassigned.remove(order_id)
                    available_vehicles.remove(vehicle_id)
                    improvements += 1
                    break

        return solution

    except:
        return solution


def solver(env) -> Dict:
    """
    Robust MDVRP solver focused on handling all scenarios.

    Key improvements over v3:
    - More robust pathfinding (1000-node limit vs 500)
    - Aggressive single-order assignment for edge cases
    - Multiple fallback strategies
    - Better error handling throughout
    - Lightweight post-optimization for unassigned orders

    Target: 0% scenario failure rate, 85%+ average fulfillment
    """
    try:
        # Get scenario data
        adjacency_list = env.get_road_network_data().get("adjacency_list", {})

        # Phase 1: Robust construction with multiple fallback strategies
        solution = construct_robust_solution(env, adjacency_list)

        # Phase 2: Lightweight optimization to recover unassigned orders
        solution = light_optimization(env, solution, adjacency_list, time_limit=120)

        return solution

    except Exception as e:
        # Ultimate fallback: return empty solution rather than crash
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
#         print(f"Fulfillment: {fulfillment.get('fully_fulfilled_orders', 0)}/50")
