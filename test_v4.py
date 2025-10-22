#!/usr/bin/env python3
"""
Test script for VibeCoders_solver_4.py
Multiple runs to test robustness
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_4 import solver
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
    print("Testing VibeCoders_solver_4.py - Robustness Focused")
    print("=" * 70)

    num_runs = 10
    results = []

    for i in range(1, num_runs + 1):
        print(f"\nRun {i}/{num_runs}...")
        result = run_test(i)
        results.append(result)

        if result['valid']:
            print(f"  ✓ {result['fulfilled']}/{result['total']} orders ({result['fulfillment']:.1f}%)")
            print(f"    Cost: ${result['cost']:,.2f}, Routes: {result['routes']}, Time: {result['time']:.1f}s")
        else:
            print(f"  ✗ Invalid: {result.get('message', 'Unknown error')}")

    # Summary
    valid_results = [r for r in results if r['valid']]

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if valid_results:
        fulfillments = [r['fulfillment'] for r in valid_results]
        costs = [r['cost'] for r in valid_results]
        times = [r['time'] for r in valid_results]
        routes = [r['routes'] for r in valid_results]

        print(f"Valid runs:         {len(valid_results)}/{num_runs}")
        print(f"Fulfillment:        {min(fulfillments):.1f}% - {max(fulfillments):.1f}% (avg {sum(fulfillments)/len(fulfillments):.1f}%)")
        print(f"Cost:               ${min(costs):,.2f} - ${max(costs):,.2f} (avg ${sum(costs)/len(costs):,.2f})")
        print(f"Routes:             {min(routes)} - {max(routes)} (avg {sum(routes)/len(routes):.1f})")
        print(f"Time:               {min(times):.1f}s - {max(times):.1f}s (avg {sum(times)/len(times):.1f}s)")

        print("\n" + "=" * 70)

        avg_fulfillment = sum(fulfillments) / len(fulfillments)
        zero_failures = sum(1 for f in fulfillments if f == 0)
        low_failures = sum(1 for f in fulfillments if f < 50)

        print(f"Zero-fulfillment failures: {zero_failures}/{len(valid_results)}")
        print(f"Low-fulfillment (<50%):    {low_failures}/{len(valid_results)}")

        if zero_failures == 0 and avg_fulfillment >= 85:
            print("\n🎉 EXCELLENT: No failures, 85%+ average")
        elif zero_failures == 0 and avg_fulfillment >= 75:
            print("\n✓ STRONG: No failures, 75%+ average")
        elif zero_failures == 0:
            print("\n✓ GOOD: No failures (robustness achieved)")
        else:
            print("\n⚠ NEEDS WORK: Still has failure cases")

        print("\nComparison to v3:")
        print("  v3: 89.2% avg, but 0% and 11% failures in competition")
        print(f"  v4: {avg_fulfillment:.1f}% avg, {zero_failures} failures in {len(valid_results)} runs")

    else:
        print("⚠ All runs failed!")


if __name__ == '__main__':
    main()
