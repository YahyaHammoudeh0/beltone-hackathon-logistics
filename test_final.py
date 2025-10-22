#!/usr/bin/env python3
"""Test final solver"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_final import solver

env = LogisticsEnvironment()
print("Testing final solver with fallback logic...\n")

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
unfulfilled = []
for order_id in env.get_all_order_ids():
    status = env.get_order_fulfillment_status(order_id)
    remaining = status.get('remaining', {})
    if all(qty == 0 for qty in remaining.values()):
        fulfilled += 1
    else:
        unfulfilled.append(order_id)

stats = env.get_solution_statistics(result, details)

print(f"\n{'='*60}")
print(f"FINAL PERFORMANCE")
print(f"{'='*60}")
print(f"Orders Fulfilled: {fulfilled}/50 ({100*fulfilled/50:.1f}%)")
print(f"Unfulfilled: {len(unfulfilled)} - {unfulfilled[:10]}")
print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
print(f"Vehicles Used: {len(result['routes'])}/12")

if fulfilled == 50:
    print(f"\n{'✓'*20}")
    print(f"PERFECT! 100% FULFILLMENT ACHIEVED!")
    print(f"{'✓'*20}")
else:
    remaining_pct = 100 * (50 - fulfilled) / 50
    print(f"\n⚠️  {50-fulfilled} orders unfulfilled = {remaining_pct:.1f}% penalty")
    print(f"Need to improve fulfillment rate")
