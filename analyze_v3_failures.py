#!/usr/bin/env python3
"""
Analyze VibeCoders_solver_3.py failures on different scenarios
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_3 import construct_initial_solution
import random


def analyze_initial_construction():
    """Test initial construction on multiple random seeds."""
    print("=" * 70)
    print("Analyzing Initial Construction Robustness")
    print("=" * 70)

    results = []

    for seed in range(10):
        # Set random seed for reproducibility
        random.seed(seed)

        env = LogisticsEnvironment()
        adjacency_list = env.get_road_network_data().get("adjacency_list", {})

        print(f"\nSeed {seed}:")

        # Test initial construction
        routes, assigned = construct_initial_solution(env, adjacency_list)

        total_orders = len(env.get_all_order_ids())
        fulfillment = len(assigned)
        pct = (fulfillment / total_orders * 100) if total_orders else 0

        print(f"  Initial: {fulfillment}/{total_orders} orders ({pct:.1f}%)")

        # Analyze what went wrong if low fulfillment
        if pct < 50:
            print(f"  ⚠ LOW FULFILLMENT - Investigating...")

            # Check if any routes were created
            print(f"    Routes created: {len(routes)}")

            # Check vehicles
            vehicles = env.get_available_vehicles()
            print(f"    Available vehicles: {len(vehicles)}")

            # Check warehouses
            warehouses = env.warehouses
            print(f"    Warehouses: {len(warehouses)}")

            # Try to understand order properties
            unassigned = set(env.get_all_order_ids()) - assigned
            print(f"    Unassigned orders: {len(unassigned)}")

            # Sample some unassigned orders
            for order_id in list(unassigned)[:3]:
                order_node = env.get_order_location(order_id)
                print(f"      Order {order_id}: node {order_node}")

                # Check connectivity from warehouses
                for wh in list(warehouses.values())[:2]:
                    wh_node = wh.location.id
                    try:
                        dist = env.get_distance(wh_node, order_node)
                        print(f"        Distance from WH {wh.id}: {dist:.2f} km" if dist else "        No path from WH")
                    except:
                        print(f"        Error getting distance from WH {wh.id}")

        results.append({
            'seed': seed,
            'fulfillment': pct,
            'routes': len(routes),
            'assigned': fulfillment,
            'total': total_orders
        })

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    fulfillments = [r['fulfillment'] for r in results]
    print(f"Average fulfillment: {sum(fulfillments)/len(fulfillments):.1f}%")
    print(f"Min fulfillment: {min(fulfillments):.1f}%")
    print(f"Max fulfillment: {max(fulfillments):.1f}%")

    failures = [r for r in results if r['fulfillment'] < 50]
    print(f"\nFailure rate (<50%): {len(failures)}/{len(results)}")

    if failures:
        print("\nFailed scenarios:")
        for f in failures:
            print(f"  Seed {f['seed']}: {f['fulfillment']:.1f}% ({f['assigned']}/{f['total']} orders)")


if __name__ == '__main__':
    analyze_initial_construction()
