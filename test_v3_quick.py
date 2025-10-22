#!/usr/bin/env python3
"""
Quick test for VibeCoders_solver_3.py
Tests with short time limit (60 seconds) for validation
"""
from robin_logistics import LogisticsEnvironment
import time


# Temporarily patch the solver for quick testing
def quick_test():
    """Run a quick test with reduced time limit."""
    print("=" * 70)
    print("Quick validation test for VibeCoders_solver_3.py")
    print("Time limit: 60 seconds (instead of 25 minutes)")
    print("=" * 70)

    # Import and modify the solver
    import VibeCoders_solver_3 as solver_module

    env = LogisticsEnvironment()

    # Get scenario data
    adjacency_list = env.get_road_network_data().get("adjacency_list", {})

    print("\nPhase 1: Initial solution construction...")
    start = time.time()
    routes, assigned = solver_module.construct_initial_solution(env, adjacency_list)
    elapsed = time.time() - start

    print(f"✓ Initial solution created in {elapsed:.1f}s")
    print(f"  Routes: {len(routes)}")
    print(f"  Orders assigned: {len(assigned)}")

    initial_fulfillment = len(assigned)
    initial_cost = sum(r.cost for r in routes)

    print(f"  Initial fulfillment: {len(assigned)}/{len(env.get_all_order_ids())}")
    print(f"  Initial cost: ${initial_cost:,.2f}")

    print("\nPhase 2: ALNS optimization (60 seconds)...")
    start = time.time()
    routes, assigned = solver_module.alns_optimize(
        env, routes, assigned, adjacency_list, time_limit=60
    )
    elapsed = time.time() - start

    print(f"✓ ALNS optimization completed in {elapsed:.1f}s")
    print(f"  Routes: {len(routes)}")
    print(f"  Orders assigned: {len(assigned)}")

    final_fulfillment = len(assigned)
    final_cost = sum(r.cost for r in routes)

    print(f"  Final fulfillment: {len(assigned)}/{len(env.get_all_order_ids())}")
    print(f"  Final cost: ${final_cost:,.2f}")

    print("\nPhase 3: Converting to solution format...")
    solution = {"routes": []}

    for route in routes:
        if not route.orders:
            continue
        route_dict = solver_module.create_route_dict(env, route, adjacency_list)
        if route_dict:
            solution['routes'].append(route_dict)

    print(f"✓ Solution created with {len(solution['routes'])} routes")

    print("\nValidating solution...")
    is_valid, msg, details = env.validate_solution_complete(solution)

    print(f"Valid: {'✓' if is_valid else '✗'} {is_valid}")
    print(f"Message: {msg}")

    if is_valid:
        stats = env.get_solution_statistics(solution, details)
        fulfillment = env.get_solution_fulfillment_summary(solution, details)

        fulfilled = fulfillment.get('fully_fulfilled_orders', 0)
        total = len(env.get_all_order_ids())
        pct = (fulfilled / total * 100) if total else 0

        print("\n" + "=" * 70)
        print("QUICK TEST RESULTS (60 second limit)")
        print("=" * 70)
        print(f"Fulfillment:    {fulfilled}/{total} orders ({pct:.1f}%)")
        print(f"Cost:           ${stats.get('total_cost', 0):,.2f}")
        print(f"Distance:       {stats.get('total_distance', 0):,.2f} km")
        print("=" * 70)

        print("\nImprovement from initial to final:")
        print(f"  Fulfillment: {initial_fulfillment} → {final_fulfillment} ({final_fulfillment - initial_fulfillment:+d} orders)")
        print(f"  Cost: ${initial_cost:,.2f} → ${final_cost:,.2f}")

        if pct >= 85:
            print("\n✓ Excellent: 85%+ fulfillment in quick test")
        elif pct >= 75:
            print("\n✓ Good: 75%+ fulfillment in quick test")
        else:
            print("\n⚠ Needs improvement: <75% fulfillment")

        print("\nNote: Full 25-minute optimization may achieve significantly better results")

    return is_valid


if __name__ == '__main__':
    quick_test()
