#!/usr/bin/env python3
"""Analyze which routes fail and why"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

env = LogisticsEnvironment()
result = solver(env)

print(f"Total routes: {len(result['routes'])}\n")

# Validate each route individually
for i, route in enumerate(result['routes']):
    vehicle_id = route.get('vehicle_id')
    steps = route.get('steps', [])

    # Get vehicle details
    vehicle = env.get_vehicle_by_id(vehicle_id)

    # Count orders in this route
    orders_in_route = set()
    for step in steps:
        for delivery in step.get('deliveries', []):
            orders_in_route.add(delivery.get('order_id'))

    # Calculate total distance
    total_distance = 0
    prev_node = None
    for step in steps:
        node_id = step.get('node_id')
        if prev_node is not None:
            try:
                dist = env.get_distance(prev_node, node_id)
                total_distance += dist if dist else 0
            except:
                pass
        prev_node = node_id

    print(f"Route {i+1}: {vehicle_id}")
    print(f"  Vehicle type: {vehicle.type}")
    print(f"  Max distance: {vehicle.max_distance} km")
    print(f"  Orders: {len(orders_in_route)} - {sorted(orders_in_route)}")
    print(f"  Steps: {len(steps)}")
    print(f"  Total distance: {total_distance:.2f} km")
    print(f"  Distance OK: {total_distance <= vehicle.max_distance}")

    # Check capacity
    total_weight = 0
    total_volume = 0
    for order_id in orders_in_route:
        requirements = env.get_order_requirements(order_id)
        for sku_id, qty in requirements.items():
            sku = env.skus[sku_id]
            total_weight += sku.weight * qty
            total_volume += sku.volume * qty

    print(f"  Weight: {total_weight:.1f}/{vehicle.capacity_weight} kg")
    print(f"  Volume: {total_volume:.1f}/{vehicle.capacity_volume} m³")
    print(f"  Capacity OK: {total_weight <= vehicle.capacity_weight and total_volume <= vehicle.capacity_volume}")

    # Try to execute this route alone
    print(f"  Testing execution...")
    test_env = LogisticsEnvironment()
    test_solution = {'routes': [route]}
    success, msg = test_env.execute_solution(test_solution)
    print(f"  Execution result: {msg}")
    print()

# Now execute all together
print("="*60)
print("FULL EXECUTION TEST")
print("="*60)
success, msg = env.execute_solution(result)
print(f"Result: {msg}")

# Count actual fulfillment
fulfilled = 0
for order_id in env.get_all_order_ids():
    status = env.get_order_fulfillment_status(order_id)
    remaining = status.get('remaining', {})
    if all(qty == 0 for qty in remaining.values()):
        fulfilled += 1

print(f"\nOrders fulfilled: {fulfilled}/50")
print(f"Unfulfilled: {50 - fulfilled}")
