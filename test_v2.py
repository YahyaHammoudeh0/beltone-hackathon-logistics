#!/usr/bin/env python3
"""Test solver v2"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_2 import solver

env = LogisticsEnvironment()
print("Testing simple 1-order-per-vehicle solver...\n")

result = solver(env)
print(f"Routes created: {len(result['routes'])}")

# Validate
is_valid, msg, details = env.validate_solution_complete(result)
print(f"Valid: {is_valid}")

if not is_valid:
    print(f"Validation failed: {msg}")
    exit(1)

# Execute
print("\nExecuting...")
success, exec_msg = env.execute_solution(result)
print(f"Execution: {exec_msg}")

# Count fulfillment
fulfilled = 0
for order_id in env.get_all_order_ids():
    status = env.get_order_fulfillment_status(order_id)
    remaining = status.get('remaining', {})
    if all(qty == 0 for qty in remaining.values()):
        fulfilled += 1

stats = env.get_solution_statistics(result, details)

print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"Orders Fulfilled: {fulfilled}/50 ({100*fulfilled/50:.0f}%)")
print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
print(f"Vehicles Used: {len(result['routes'])}/12")

if fulfilled == 50:
    print(f"\n✓✓✓ PERFECT! 100% FULFILLMENT! ✓✓✓")
else:
    print(f"\n⚠️  Still missing {50-fulfilled} orders")
