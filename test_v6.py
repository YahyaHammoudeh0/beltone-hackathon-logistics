#!/usr/bin/env python3
"""
Test script for VibeCoders_solver_6.py
Dijkstra-based pathfinding approach
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_6 import solver
import time


def run_test(run_num):
    """Run a single test."""
    env = LogisticsEnvironment()

    start = time.time()
    result = solver(env)
    elapsed = time.time() - start

    is_valid, msg, details = env.validate_solution_complete(result)

    if is_valid:
        stats = env.get_solution_statistics(result, details)
        fulfillment = env.get_solution_fulfillment_summary(result, details)

        fulfilled = fulfillment.get('fully_fulfilled_orders', 0)
        total = len(env.get_all_order_ids())
        pct = (fulfilled / total * 100) if total else 0
        cost = stats.get('total_cost', 0)
        distance = stats.get('total_distance', 0)

        return {
            'run': run_num,
            'valid': True,
            'fulfillment': pct,
            'fulfilled': fulfilled,
            'total': total,
            'cost': cost,
            'distance': distance,
            'routes': len(result['routes']),
            'time': elapsed
        }
    else:
        return {
            'run': run_num,
            'valid': False,
            'time': elapsed,
            'message': msg
        }


def main():
    """Run multiple tests."""
    print("=" * 70)
    print("Testing VibeCoders_solver_6.py - Dijkstra Pathfinding")
    print("KEY CHANGE: BFS → Dijkstra (true shortest path by distance)")
    print("=" * 70)

    num_runs = 10
    results = []

    for i in range(1, num_runs + 1):
        print(f"\nRun {i}/{num_runs}...")
        result = run_test(i)
        results.append(result)

        if result['valid']:
            print(f"  ✓ {result['fulfilled']}/{result['total']} orders ({result['fulfillment']:.1f}%)")
            print(f"    Cost: ${result['cost']:,.2f}, Distance: {result['distance']:.2f} km")
            print(f"    Routes: {result['routes']}, Time: {result['time']:.2f}s")
        else:
            print(f"  ✗ Invalid: {result.get('message', 'Unknown error')}")

    # Summary
    valid_results = [r for r in results if r['valid']]

    print("\n" + "=" * 70)
    print("SUMMARY - V6 (Dijkstra Pathfinding)")
    print("=" * 70)

    if valid_results:
        fulfillments = [r['fulfillment'] for r in valid_results]
        costs = [r['cost'] for r in valid_results]
        distances = [r['distance'] for r in valid_results]
        times = [r['time'] for r in valid_results]
        routes = [r['routes'] for r in valid_results]

        print(f"Valid runs:         {len(valid_results)}/{num_runs}")
        print(f"Fulfillment:        {min(fulfillments):.1f}% - {max(fulfillments):.1f}% (avg {sum(fulfillments)/len(fulfillments):.1f}%)")
        print(f"Cost:               ${min(costs):,.2f} - ${max(costs):,.2f} (avg ${sum(costs)/len(costs):,.2f})")
        print(f"Distance:           {min(distances):.2f} - {max(distances):.2f} km (avg {sum(distances)/len(distances):.2f} km)")
        print(f"Routes:             {min(routes)} - {max(routes)} (avg {sum(routes)/len(routes):.1f})")
        print(f"Time:               {min(times):.2f}s - {max(times):.2f}s (avg {sum(times)/len(times):.2f}s)")

        print("\n" + "=" * 70)

        avg_fulfillment = sum(fulfillments) / len(fulfillments)
        avg_distance = sum(distances) / len(distances)
        zero_failures = sum(1 for f in fulfillments if f == 0)
        low_failures = sum(1 for f in fulfillments if f < 50)

        print(f"Zero-fulfillment failures:  {zero_failures}/{len(valid_results)}")
        print(f"Low-fulfillment (<50%):     {low_failures}/{len(valid_results)}")

        print("\n" + "=" * 70)
        print("COMPARISON TO PREVIOUS VERSIONS")
        print("=" * 70)
        print("  v3: 89.2% avg, but 0% and 11% failures in competition")
        print("  v4: 76.2% avg (BFS 2000-node), 0% and 11% failures in competition")
        print("  v5: 24.0% avg (single-order, caps at 24%)")
        print(f"  v6: {avg_fulfillment:.1f}% avg (Dijkstra), {zero_failures} failures in {len(valid_results)} runs")

        print("\n" + "=" * 70)
        print("KEY INNOVATION: Dijkstra vs BFS")
        print("=" * 70)
        print("  BFS:      Finds shortest path by NUMBER OF HOPS")
        print("  Dijkstra: Finds shortest path by ACTUAL DISTANCE")
        print(f"  Avg distance: {avg_distance:.2f} km")

        if zero_failures == 0:
            print("\n✓ No zero-fulfillment failures locally")
        else:
            print(f"\n⚠ {zero_failures} zero-fulfillment failures")

        if avg_fulfillment >= 85:
            print("✓ Strong average fulfillment (85%+)")
        elif avg_fulfillment >= 75:
            print("~ Good average fulfillment (75%+)")
        else:
            print("⚠ Below target average (<75%)")

        print("\nNext step: Submit V6 to competition, check scenario 4 performance")

    else:
        print("⚠ All runs failed!")


if __name__ == '__main__':
    main()
