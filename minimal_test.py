#!/usr/bin/env python3
"""Minimal test to understand fulfillment"""
from robin_logistics import LogisticsEnvironment

if __name__ == '__main__':
    env = LogisticsEnvironment()

    # Get basic info
    orders = env.get_all_order_ids()
    vehicles = env.get_available_vehicles()

    print(f"Total orders: {len(orders)}")
    print(f"Total vehicles: {len(vehicles)}\n")

    # Check initial order status
    print("Checking initial order statuses...")
    statuses = {}
    for order_id in orders[:5]:  # Just check first 5
        status = env.get_order_fulfillment_status(order_id)
        statuses[order_id] = status
        print(f"  {order_id}: {status}")

    # Try a minimal solution - empty
    solution = {"routes": []}

    # Validate empty solution
    is_valid, msg, details = env.validate_solution_complete(solution)
    print(f"\nEmpty solution valid: {is_valid}")
    print(f"Message: {msg}")

    if details:
        fulfillment = env.get_solution_fulfillment_summary(solution, details)
        print(f"Fulfillment: {fulfillment}")
