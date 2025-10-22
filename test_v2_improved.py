#!/usr/bin/env python3
"""Test improved v2 solver"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_2_improved import solver

env = LogisticsEnvironment()
print("Testing IMPROVED solver v2 (research-inspired)...\n")

result = solver(env)
print(f"Routes created: {len(result['routes'])}")

# Validate
is_valid, msg, details = env.validate_solution_complete(result)
print(f"Valid: {is_valid}")

if not is_valid:
    print(f"Failed: {msg}")
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
print(f"RESULTS")
print(f"{'='*60}")
print(f"Orders Fulfilled: {fulfilled}/50 ({100*fulfilled/50:.0f}%)")
if unfulfilled:
    print(f"Unfulfilled: {unfulfilled}")
print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
print(f"Vehicles Used: {len(result['routes'])}/12")
print(f"Routes Executed: {exec_msg}")

if fulfilled == 50:
    print(f"\n{'🎉'*20}")
    print(f"PERFECT! 100% FULFILLMENT ACHIEVED!")
    print(f"{'🎉'*20}")
    print(f"\nNow optimizing for SHORTEST DISTANCE...")
else:
    pct = 100 * fulfilled / 50
    print(f"\n📊 Fulfillment: {pct:.1f}% - {50-fulfilled} orders remaining")
