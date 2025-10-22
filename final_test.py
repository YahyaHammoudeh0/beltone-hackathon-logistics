#!/usr/bin/env python3
"""Final test with execution"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

env = LogisticsEnvironment()
print("Generating solution...")
result = solver(env)

print(f"\nRoutes created: {len(result['routes'])}")

# Validate
is_valid, msg, details = env.validate_solution_complete(result)
print(f"Valid: {is_valid}")

if not is_valid:
    print(f"Validation failed: {msg}")
    exit(1)

# Execute
print("\nExecuting solution...")
success, exec_msg = env.execute_solution(result)
print(f"Execution: {exec_msg}")

# Count fulfilled orders AFTER execution
fulfilled = 0
for order_id in env.get_all_order_ids():
    status = env.get_order_fulfillment_status(order_id)
    remaining = status.get('remaining', {})
    if all(qty == 0 for qty in remaining.values()):
        fulfilled += 1

# Get statistics
stats = env.get_solution_statistics(result, details)

print(f"\n{'='*60}")
print("FINAL PERFORMANCE")
print(f"{'='*60}")
print(f"Orders Fulfilled: {fulfilled}/50 ({100*fulfilled/50:.1f}%)")
print(f"Total Cost: ${stats.get('total_cost', 0):,.2f}")
print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
print(f"Vehicles Used: {len(result['routes'])}/12")

# Score estimation
if fulfilled < 50:
    unfulfilled_pct = 100 * (50 - fulfilled) / 50
    print(f"\n⚠️  {50-fulfilled} unfulfilled orders = {unfulfilled_pct:.1f}% penalty")
    print(f"Penalty factor will multiply benchmark cost significantly!")
else:
    print(f"\n✓ Perfect fulfillment! Competing on cost optimization only.")
    print(f"Lower cost = better ranking")
