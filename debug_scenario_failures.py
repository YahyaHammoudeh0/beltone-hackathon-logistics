#!/usr/bin/env python3
"""
Debug why VibeCoders solvers fail on certain scenarios
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_4 import solver, create_single_order_route, find_shortest_path_robust
import random


def analyze_scenario(seed=None):
    """Analyze a scenario in detail."""
    if seed is not None:
        random.seed(seed)

    env = LogisticsEnvironment()

    print("=" * 70)
    print(f"Scenario Analysis (seed={seed})")
    print("=" * 70)

    # Basic scenario info
    orders = env.get_all_order_ids()
    vehicles = env.get_available_vehicles()
    warehouses = env.warehouses

    print(f"\nScenario Overview:")
    print(f"  Orders: {len(orders)}")
    print(f"  Vehicles: {len(vehicles)}")
    print(f"  Warehouses: {len(warehouses)}")

    # Analyze road network
    road_network = env.get_road_network_data()
    adjacency_list = road_network.get("adjacency_list", {})
    print(f"  Road network nodes: {len(adjacency_list)}")

    # Check vehicle details
    print(f"\nVehicle Fleet:")
    vehicle_types = {}
    for vid in vehicles:
        v = env.get_vehicle_by_id(vid)
        if v:
            vtype = v.type
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
    for vtype, count in vehicle_types.items():
        print(f"  {vtype}: {count}")

    # Check order connectivity
    print(f"\nOrder Connectivity Analysis:")
    unreachable_orders = []

    for i, order_id in enumerate(orders[:10]):  # Check first 10
        order_node = env.get_order_location(order_id)
        print(f"\n  Order {i+1}/{len(orders)} (ID: {order_id}):")
        print(f"    Location node: {order_node}")

        if order_node is None:
            print(f"    ⚠ Order has no location!")
            unreachable_orders.append(order_id)
            continue

        # Check connectivity from each warehouse
        reachable_from = []
        for wh_id, wh in list(warehouses.items())[:3]:  # Check first 3 warehouses
            wh_node = wh.location.id

            # Try pathfinding
            path = find_shortest_path_robust(wh_node, order_node, adjacency_list, max_length=1000)
            if path:
                path_len = len(path)
                reachable_from.append(wh_id)
                print(f"    ✓ Reachable from WH {wh_id} (path length: {path_len})")
            else:
                print(f"    ✗ NOT reachable from WH {wh_id}")

        if not reachable_from:
            print(f"    ⚠ Order NOT reachable from any warehouse!")
            unreachable_orders.append(order_id)

    if unreachable_orders:
        print(f"\n⚠ WARNING: {len(unreachable_orders)} orders are unreachable!")
        print(f"  This explains 0% fulfillment scenarios")

    # Try solver
    print(f"\n{'=' * 70}")
    print("Running Solver...")
    print("=" * 70)

    result = solver(env)

    print(f"\nSolver Result:")
    print(f"  Routes created: {len(result['routes'])}")

    is_valid, msg, details = env.validate_solution_complete(result)
    print(f"  Valid: {is_valid}")
    print(f"  Message: {msg}")

    if is_valid:
        fulfillment = env.get_solution_fulfillment_summary(result, details)
        stats = env.get_solution_statistics(result, details)

        fulfilled = fulfillment.get('fully_fulfilled_orders', 0)
        total = len(orders)
        pct = (fulfilled / total * 100) if total else 0

        print(f"\n  Fulfillment: {fulfilled}/{total} ({pct:.1f}%)")
        print(f"  Cost: ${stats.get('total_cost', 0):,.2f}")

        if pct < 50:
            print(f"\n  ⚠ LOW FULFILLMENT - Possible causes:")
            print(f"    - Unreachable orders: {len(unreachable_orders)}")
            print(f"    - Pathfinding limitations")
            print(f"    - Capacity constraints")

    return {
        'orders': len(orders),
        'vehicles': len(vehicles),
        'routes': len(result['routes']),
        'unreachable': len(unreachable_orders),
        'valid': is_valid
    }


def main():
    """Run analysis on multiple scenarios."""
    print("Testing multiple scenarios to find failure patterns\n")

    results = []
    for seed in range(10):
        result = analyze_scenario(seed)
        results.append(result)
        print(f"\n{'=' * 70}\n")

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for i, r in enumerate(results):
        status = "✓" if r['valid'] else "✗"
        print(f"Seed {i}: {status} Valid={r['valid']}, Routes={r['routes']}, Unreachable={r['unreachable']}")


if __name__ == '__main__':
    # Test a few scenarios
    for seed in [0, 1, 2]:
        analyze_scenario(seed)
        print("\n\n")
