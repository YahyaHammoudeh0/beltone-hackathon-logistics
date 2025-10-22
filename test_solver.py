#!/usr/bin/env python3
"""Test the submission solver"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

if __name__ == '__main__':
    print("Testing VibeCoders_solver_1.py\n")
    print("="*60)

    env = LogisticsEnvironment()
    result = solver(env)

    print(f"Routes created: {len(result['routes'])}")
    print("\nValidating solution...")

    # Validate
    is_valid, msg, details = env.validate_solution_complete(result)
    print(f"Valid: {is_valid}")
    print(f"Message: {msg}")

    if is_valid:
        stats = env.get_solution_statistics(result, details)
        fulfillment = env.get_solution_fulfillment_summary(result, details)

        print(f"\n{'='*60}")
        print("PERFORMANCE METRICS")
        print(f"{'='*60}")
        print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
        print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
        print(f"Vehicles Used: {len(result['routes'])}/12")
        print(f"\nOrders Fulfilled: {fulfillment.get('fully_fulfilled_orders', 0)}/{fulfillment.get('total_orders', 0)}")
        print(f"Fulfillment Rate: {fulfillment.get('average_fulfillment_rate', 0):.1f}%")

        # Estimate score (without knowing benchmark)
        fulfillment_rate = fulfillment.get('average_fulfillment_rate', 0)
        unfulfilled_penalty_factor = 100 - fulfillment_rate
        total_cost = stats.get('total_cost', 0)

        print(f"\n{'='*60}")
        print("SCORING ANALYSIS")
        print(f"{'='*60}")
        print(f"Your Cost: ${total_cost:,.2f}")
        print(f"Unfulfilled Penalty Factor: {unfulfilled_penalty_factor:.1f}%")
        print(f"Note: Final score depends on benchmark solver cost")

        if fulfillment_rate < 100:
            print(f"\n⚠️  WARNING: {100-fulfillment_rate:.1f}% unfulfilled orders will add significant penalty!")
        else:
            print(f"\n✓ EXCELLENT: 100% fulfillment! Score depends only on cost optimization.")
