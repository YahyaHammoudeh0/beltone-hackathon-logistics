#!/usr/bin/env python3
"""
Vibe Coders - Beltone AI Hackathon Submission v6
Dijkstra-Based Pathfinding for True Shortest Paths

KEY CHANGE from V4:
- Replace BFS (shortest by hops) with Dijkstra (shortest by distance)
- This finds TRUE shortest path, not just fewest edges
- Should handle complex scenarios better

Hypothesis: BFS limitation is causing scenario 4 failure
- BFS: Prefers path with 100 short edges over path with 2 long edges
- Dijkstra: Finds true shortest distance path
- robin_testcase likely uses Dijkstra/A*

Target: Fix scenario 4 (currently 11%), maintain other scenarios
"""
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
import heapq


# ============================================================================
# DIJKSTRA PATHFINDING (NEW!)
# ============================================================================

def find_path_dijkstra(env, start_node: int, end_node: int, adjacency_list: Dict, max_distance: float = float('inf')) -> Optional[List[int]]:
    """
    Find TRUE shortest path by distance using Dijkstra's algorithm.

    This is the key improvement over BFS:
    - BFS finds shortest path by number of hops
    - Dijkstra finds shortest path by actual distance
    - Critical for scenarios with varied edge lengths
    """
    if start_node is None or end_node is None:
        return None

    if start_node == end_node:
        return [start_node]

    try:
        # Dijkstra setup
        distances = {start_node: 0.0}
        previous = {}
        pq = [(0.0, start_node)]  # (distance, node)
        visited = set()

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            # Found destination
            if current_node == end_node:
                # Reconstruct path
                path = []
                node = end_node
                while node in previous:
                    path.append(node)
                    node = previous[node]
                path.append(start_node)
                return path[::-1]

            # Already processed
            if current_node in visited:
                continue

            # Don't explore if too far
            if current_dist > max_distance:
                continue

            visited.add(current_node)

            # Explore neighbors
            neighbors = adjacency_list.get(current_node, [])
            for neighbor in neighbors:
                try:
                    neighbor_int = int(neighbor) if hasattr(neighbor, '__int__') else neighbor
                    if neighbor_int is None or neighbor_int in visited:
                        continue

                    # Get actual edge distance from environment
                    edge_dist = env.get_distance(current_node, neighbor_int)
                    if edge_dist is None or edge_dist <= 0:
                        continue

                    new_dist = current_dist + edge_dist

                    # Update if better path found
                    if neighbor_int not in distances or new_dist < distances[neighbor_int]:
                        distances[neighbor_int] = new_dist
                        previous[neighbor_int] = current_node
                        heapq.heappush(pq, (new_dist, neighbor_int))

                except Exception as e:
                    continue

        return None  # No path found

    except Exception as e:
        return None


# ============================================================================
# FALLBACK: BFS (if Dijkstra fails)
# ============================================================================

def find_path_bfs_fallback(start_node: int, end_node: int, adjacency_list: Dict, max_length: int = 2000) -> Optional[List[int]]:
    """
    Fallback BFS pathfinding if Dijkstra fails.
    """
    if start_node is None or end_node is None:
        return None

    if start_node == end_node:
        return [start_node]

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
                    if neighbor_int is None or neighbor_int in visited:
                        continue

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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_order_size(env, order_id: str) -> Tuple[float, float]:
    """Calculate order weight and volume."""
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


def can_fit_orders(env, vehicle_id: str, order_ids: List[str]) -> bool:
    """Check if orders fit in vehicle."""
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

        return (total_weight <= vehicle.capacity_weight * 0.95 and
                total_volume <= vehicle.capacity_volume * 0.95)
    except:
        return False


def check_warehouse_inventory(env, warehouse_id: str, order_ids: List[str]) -> bool:
    """Check warehouse inventory."""
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


# ============================================================================
# ROUTE CREATION WITH DIJKSTRA
# ============================================================================

def create_single_order_route(env, vehicle_id: str, order_id: str, adjacency_list: Dict) -> Optional[Dict]:
    """Create single-order route using Dijkstra pathfinding."""
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

        # Check capacity and inventory
        if not can_fit_orders(env, vehicle_id, [order_id]):
            return None

        if not check_warehouse_inventory(env, warehouse.id, [order_id]):
            return None

        # Get order location
        order_node = env.get_order_location(order_id)
        if order_node is None:
            return None

        # Find path using Dijkstra (with fallback to BFS)
        path_to_order = find_path_dijkstra(env, home_node, order_node, adjacency_list, max_distance=1000.0)
        if not path_to_order:
            path_to_order = find_path_bfs_fallback(home_node, order_node, adjacency_list, max_length=2000)
        if not path_to_order:
            return None

        # Find path back
        path_home = find_path_dijkstra(env, order_node, home_node, adjacency_list, max_distance=1000.0)
        if not path_home:
            path_home = find_path_bfs_fallback(order_node, home_node, adjacency_list, max_length=2000)
        if not path_home:
            return None

        # Build route
        requirements = env.get_order_requirements(order_id)
        pickups = [{'warehouse_id': warehouse.id, 'sku_id': sid, 'quantity': q}
                   for sid, q in requirements.items()]
        deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                      for sid, q in requirements.items()]

        steps = []
        steps.append({'node_id': home_node, 'pickups': pickups, 'deliveries': [], 'unloads': []})

        for i in range(1, len(path_to_order) - 1):
            steps.append({'node_id': path_to_order[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

        for i in range(1, len(path_home) - 1):
            steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

        return {'vehicle_id': vehicle_id, 'steps': steps}

    except:
        return None


def create_multi_order_route(env, vehicle_id: str, order_ids: List[str], adjacency_list: Dict) -> Optional[Dict]:
    """Create multi-order route using Dijkstra pathfinding."""
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

        # Check feasibility
        if not can_fit_orders(env, vehicle_id, order_ids):
            return None

        if not check_warehouse_inventory(env, warehouse.id, order_ids):
            return None

        # Optimize sequence (nearest neighbor with Dijkstra)
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
                        dist = env.get_distance(current, order_node)
                        if dist and dist < min_dist:
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

        current_node = home_node
        for order_id in optimized_orders:
            order_node = env.get_order_location(order_id)
            if order_node is None:
                return None

            # Use Dijkstra with BFS fallback
            path = find_path_dijkstra(env, current_node, order_node, adjacency_list, max_distance=1000.0)
            if not path:
                path = find_path_bfs_fallback(current_node, order_node, adjacency_list, max_length=2000)
            if not path:
                return None

            for i in range(1, len(path) - 1):
                steps.append({'node_id': path[i], 'pickups': [], 'deliveries': [], 'unloads': []})

            requirements = env.get_order_requirements(order_id)
            deliveries = [{'order_id': order_id, 'sku_id': sid, 'quantity': q}
                         for sid, q in requirements.items()]
            steps.append({'node_id': order_node, 'pickups': [], 'deliveries': deliveries, 'unloads': []})

            current_node = order_node

        # Return home
        path_home = find_path_dijkstra(env, current_node, home_node, adjacency_list, max_distance=1000.0)
        if not path_home:
            path_home = find_path_bfs_fallback(current_node, home_node, adjacency_list, max_length=2000)
        if not path_home:
            return None

        for i in range(1, len(path_home) - 1):
            steps.append({'node_id': path_home[i], 'pickups': [], 'deliveries': [], 'unloads': []})

        steps.append({'node_id': home_node, 'pickups': [], 'deliveries': [], 'unloads': []})

        return {'vehicle_id': vehicle_id, 'steps': steps}

    except:
        return None


# ============================================================================
# MAIN SOLVER
# ============================================================================

def solver(env) -> Dict:
    """
    V6: Dijkstra-based pathfinding solver.

    Key innovation: Use Dijkstra instead of BFS for true shortest paths.
    Hypothesis: This will fix scenario 4 failure (11% → 80%+).
    """
    solution = {"routes": []}

    try:
        order_ids = env.get_all_order_ids()
        vehicle_ids = env.get_available_vehicles()
        adjacency_list = env.get_road_network_data().get("adjacency_list", {})

        if not order_ids or not vehicle_ids:
            return solution

        # Sort orders by size (largest first)
        orders_with_size = []
        for oid in order_ids:
            weight, volume = calculate_order_size(env, oid)
            orders_with_size.append((oid, weight, volume))
        orders_with_size.sort(key=lambda x: x[1], reverse=True)
        sorted_orders = [oid for oid, _, _ in orders_with_size]

        assigned = set()
        used_vehicles = set()

        # Strategy 1: Multi-order assignment
        for vehicle_id in vehicle_ids:
            if len(assigned) >= len(order_ids):
                break

            vehicle = env.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                continue

            max_orders = {'LightVan': 4, 'MediumTruck': 5, 'HeavyTruck': 5}.get(vehicle.type, 4)

            vehicle_orders = []
            for order_id in sorted_orders:
                if order_id in assigned:
                    continue
                if len(vehicle_orders) >= max_orders:
                    break

                test_orders = vehicle_orders + [order_id]
                if can_fit_orders(env, vehicle_id, test_orders):
                    warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
                    if warehouse and check_warehouse_inventory(env, warehouse.id, test_orders):
                        vehicle_orders.append(order_id)

            # Try to create route with fallback
            if vehicle_orders:
                route = None
                if len(vehicle_orders) > 1:
                    route = create_multi_order_route(env, vehicle_id, vehicle_orders, adjacency_list)

                if not route and len(vehicle_orders) > 2:
                    route = create_multi_order_route(env, vehicle_id, vehicle_orders[:len(vehicle_orders)//2], adjacency_list)
                    if route:
                        vehicle_orders = vehicle_orders[:len(vehicle_orders)//2]

                if not route and vehicle_orders:
                    route = create_single_order_route(env, vehicle_id, vehicle_orders[0], adjacency_list)
                    if route:
                        vehicle_orders = [vehicle_orders[0]]

                if route:
                    solution['routes'].append(route)
                    assigned.update(vehicle_orders)
                    used_vehicles.add(vehicle_id)

        # Strategy 2: Single-order recovery
        remaining = [oid for oid in sorted_orders if oid not in assigned]
        unused_vehicles = [vid for vid in vehicle_ids if vid not in used_vehicles]

        for vehicle_id in unused_vehicles:
            if not remaining:
                break

            for order_id in remaining[:]:
                route = create_single_order_route(env, vehicle_id, order_id, adjacency_list)
                if route:
                    solution['routes'].append(route)
                    remaining.remove(order_id)
                    assigned.add(order_id)
                    break

        return solution

    except:
        return {"routes": []}


# # COMMENT OUT THIS SECTION WHEN SUBMITTING
# if __name__ == '__main__':
#     from robin_logistics import LogisticsEnvironment
#     env = LogisticsEnvironment()
#     result = solver(env)
#
#     print(f"Routes created: {len(result['routes'])}")
#
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
