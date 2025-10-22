#!/usr/bin/env python3
"""Debug the solver to see what's happening"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

env = LogisticsEnvironment()
result = solver(env)

print(f"Total routes: {len(result['routes'])}\n")

# Check what orders are being assigned
all_order_ids_in_routes = set()
for i, route in enumerate(result['routes']):
    vehicle_id = route.get('vehicle_id')
    steps = route.get('steps', [])

    # Find deliveries
    deliveries_in_route = []
    for step in steps:
        for delivery in step.get('deliveries', []):
            order_id = delivery.get('order_id')
            if order_id:
                deliveries_in_route.append(order_id)
                all_order_ids_in_routes.add(order_id)

    print(f"Route {i+1} ({vehicle_id}): {len(deliveries_in_route)} deliveries - {deliveries_in_route}")
    print(f"  Total steps: {len(steps)}")

print(f"\nTotal unique orders in routes: {len(all_order_ids_in_routes)}")
print(f"Total orders in problem: {len(env.get_all_order_ids())}")

# Try executing the solution
print("\n" + "="*60)
print("Executing solution...")
success, msg = env.execute_solution(result)
print(f"Execution success: {success}")
print(f"Message: {msg}")

# Check fulfillment after execution
print("\n" + "="*60)
print("Checking fulfillment after execution...")
for order_id in list(all_order_ids_in_routes)[:5]:  # Check first 5
    status = env.get_order_fulfillment_status(order_id)
    print(f"{order_id}: Requested={status.get('requested')}, Delivered={status.get('delivered')}, Remaining={status.get('remaining')}")
