#!/usr/bin/env python3
"""
Multiple runs test for VibeCoders_solver_3.py
Tests consistency across different random seeds
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_3 import solver
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

        return {
            'run': run_num,
            'valid': True,
            'fulfillment': pct,
            'fulfilled': fulfilled,
            'total': total,
            'cost': cost,
            'time': elapsed
        }
    else:
        return {
            'run': run_num,
            'valid': False,
            'time': elapsed
        }


def main():
    """Run multiple tests."""
    print("=" * 70)
    print("Testing VibeCoders_solver_3.py - Multiple Runs")
    print("=" * 70)

    num_runs = 5
    results = []

    for i in range(1, num_runs + 1):
        print(f"\nRun {i}/{num_runs}...")
        result = run_test(i)
        results.append(result)

        if result['valid']:
            print(f"  ✓ {result['fulfilled']}/{result['total']} orders ({result['fulfillment']:.1f}%)")
            print(f"    Cost: ${result['cost']:,.2f}, Time: {result['time']:.1f}s")
        else:
            print(f"  ✗ Invalid solution")

    # Summary
    valid_results = [r for r in results if r['valid']]

    if valid_results:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        fulfillments = [r['fulfillment'] for r in valid_results]
        costs = [r['cost'] for r in valid_results]
        times = [r['time'] for r in valid_results]

        print(f"Valid runs:         {len(valid_results)}/{num_runs}")
        print(f"Fulfillment:        {min(fulfillments):.1f}% - {max(fulfillments):.1f}% (avg {sum(fulfillments)/len(fulfillments):.1f}%)")
        print(f"Cost:               ${min(costs):,.2f} - ${max(costs):,.2f} (avg ${sum(costs)/len(costs):,.2f})")
        print(f"Time:               {min(times):.1f}s - {max(times):.1f}s (avg {sum(times)/len(times):.1f}s)")

        print("\n" + "=" * 70)

        avg_fulfillment = sum(fulfillments) / len(fulfillments)

        if avg_fulfillment >= 90:
            print("🎉 EXCELLENT: 90%+ average fulfillment")
        elif avg_fulfillment >= 85:
            print("✓ STRONG: 85%+ average fulfillment")
        elif avg_fulfillment >= 80:
            print("✓ GOOD: 80%+ average fulfillment (v2 baseline)")
        else:
            print("⚠ NEEDS IMPROVEMENT: <80% average fulfillment")


if __name__ == '__main__':
    main()
