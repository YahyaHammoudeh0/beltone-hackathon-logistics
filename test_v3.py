#!/usr/bin/env python3
"""
Test script for VibeCoders_solver_3.py
Validates ALNS-based solver with research enhancements
"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_3 import solver
import time


def test_solver():
    """Run a single test of the solver."""
    print("=" * 70)
    print("Testing VibeCoders_solver_3.py (ALNS-based)")
    print("=" * 70)

    env = LogisticsEnvironment()

    print("\nRunning solver (this may take several minutes)...")
    start = time.time()
    result = solver(env)
    elapsed = time.time() - start

    print(f"\n✓ Solver completed in {elapsed:.1f} seconds")
    print(f"Routes created: {len(result['routes'])}")

    # Validate solution
    print("\nValidating solution...")
    is_valid, msg, details = env.validate_solution_complete(result)

    print(f"Valid: {'✓' if is_valid else '✗'} {is_valid}")
    print(f"Message: {msg}")

    if is_valid:
        # Get statistics
        stats = env.get_solution_statistics(result, details)
        fulfillment = env.get_solution_fulfillment_summary(result, details)

        fulfilled = fulfillment.get('fully_fulfilled_orders', 0)
        total = env.get_all_order_ids()
        pct = (fulfilled / len(total) * 100) if total else 0

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Fulfillment:    {fulfilled}/{len(total)} orders ({pct:.1f}%)")
        print(f"Cost:           ${stats.get('total_cost', 0):,.2f}")
        print(f"Distance:       {stats.get('total_distance', 0):,.2f} km")
        print(f"Vehicles used:  {len(result['routes'])}")
        print("=" * 70)

        # Compare with baseline (v2: ~80% fulfillment)
        baseline_fulfillment = 80.0
        improvement = pct - baseline_fulfillment

        print(f"\nComparison to baseline (v2):")
        print(f"  v2 baseline:     ~80% fulfillment")
        print(f"  v3 (ALNS):       {pct:.1f}% fulfillment")
        print(f"  Improvement:     {improvement:+.1f}%")

        if pct >= 90:
            print("\n🎉 TARGET ACHIEVED: 90%+ fulfillment!")
        elif pct >= 85:
            print("\n✓ Strong performance: 85%+ fulfillment")
        elif pct >= 80:
            print("\n~ Similar to baseline: 80%+ fulfillment")
        else:
            print("\n⚠ Below baseline: <80% fulfillment")
    else:
        print("\n✗ Solution is invalid!")

    return is_valid


if __name__ == '__main__':
    test_solver()
