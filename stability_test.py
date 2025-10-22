#!/usr/bin/env python3
"""Test solver stability across multiple runs"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

if __name__ == '__main__':
    print("Running 10 stability tests...\n")

    results = []
    for i in range(1, 11):
        env = LogisticsEnvironment()
        result = solver(env)
        is_valid, msg, details = env.validate_solution_complete(result)

        if is_valid:
            fulfillment = env.get_solution_fulfillment_summary(result, details)
            stats = env.get_solution_statistics(result, details)

            fulfilled = fulfillment.get('fully_fulfilled_orders', 0)
            rate = fulfillment.get('average_fulfillment_rate', 0)
            cost = stats.get('total_cost', 0)

            results.append((fulfilled, rate))
            print(f"Test {i:2d}: {fulfilled}/50 ({rate:.0f}%) - ${cost:,.2f}")
        else:
            print(f"Test {i:2d}: INVALID - {msg}")

    # Summary
    if results:
        avg_fulfilled = sum(r[0] for r in results) / len(results)
        avg_rate = sum(r[1] for r in results) / len(results)
        min_fulfilled = min(r[0] for r in results)
        max_fulfilled = max(r[0] for r in results)

        print(f"\n{'='*50}")
        print("SUMMARY")
        print(f"{'='*50}")
        print(f"Average: {avg_fulfilled:.1f}/50 ({avg_rate:.1f}%)")
        print(f"Range: {min_fulfilled}-{max_fulfilled} orders")
        print(f"Tests >= 90%: {sum(1 for r in results if r[1] >= 90)}/10")
