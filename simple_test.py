#!/usr/bin/env python3
"""Simple execution-only test"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

if __name__ == '__main__':
    # Fresh environment
    env = LogisticsEnvironment()

    print("Generating solution...")
    result = solver(env)
    print(f"Routes created: {len(result['routes'])}\n")

    # Count assigned orders
    assigned_orders = set()
    for route in result['routes']:
        for step in route['steps']:
            for delivery in step.get('deliveries', []):
                assigned_orders.add(delivery['order_id'])

    print(f"Orders assigned in solution: {len(assigned_orders)}/50\n")

    # Validate first to get details
    print("Validating...")
    is_valid, msg, details = env.validate_solution_complete(result)
    print(f"Valid: {is_valid} - {msg}\n")

    if is_valid:
        # Get fulfillment summary from validation
        fulfillment = env.get_solution_fulfillment_summary(result, details)
        print("Fulfillment Summary:")
        print(f"  Total orders: {fulfillment.get('total_orders', 0)}")
        print(f"  Orders served: {fulfillment.get('orders_served', 0)}")
        print(f"  Fully fulfilled: {fulfillment.get('fully_fulfilled_orders', 0)}")
        print(f"  Average fulfillment: {fulfillment.get('average_fulfillment_rate', 0):.1f}%\n")

        # Get stats
        stats = env.get_solution_statistics(result, details)
        print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
        print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
