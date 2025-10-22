#!/usr/bin/env python3
"""Debug why final solver creates no routes"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_final import (
    calculate_order_size, can_fit_orders, check_inventory,
    estimate_route_distance, create_route
)

env = LogisticsEnvironment()
road_network = env.get_road_network_data()
adjacency_list = road_network.get("adjacency_list", {})

vehicle_ids = env.get_available_vehicles()
order_ids = env.get_all_order_ids()

print("Testing first vehicle with first order...\n")

vehicle_id = vehicle_ids[0]
order_id = order_ids[0]

vehicle = env.get_vehicle_by_id(vehicle_id)
print(f"Vehicle: {vehicle_id} ({vehicle.type})")
print(f"  Max distance: {vehicle.max_distance} km")
print(f"  Capacity: {vehicle.capacity_weight} kg, {vehicle.capacity_volume} m³")

print(f"\nOrder: {order_id}")
weight, volume = calculate_order_size(env, order_id)
print(f"  Size: {weight} kg, {volume} m³")

print(f"\nCapacity check:")
fits = can_fit_orders(env, vehicle_id, [order_id])
print(f"  Can fit with 90% margin: {fits}")

print(f"\nInventory check:")
has_inv = check_inventory(env, vehicle.home_warehouse_id, [order_id])
print(f"  Has inventory: {has_inv}")

warehouse = env.get_warehouse_by_id(vehicle.home_warehouse_id)
order_node = env.get_order_location(order_id)

print(f"\nDistance estimation:")
estimated = estimate_route_distance(env, warehouse.location.id, [order_node])
print(f"  Estimated distance: {estimated:.2f} km")
print(f"  80% of max distance: {vehicle.max_distance * 0.8:.2f} km")
print(f"  Passes distance check: {estimated <= vehicle.max_distance * 0.8}")

print(f"\nTrying to create route...")
route = create_route(env, vehicle_id, [order_id], adjacency_list)
print(f"  Route created: {route is not None}")

if route:
    print(f"  Steps: {len(route['steps'])}")
else:
    print("  FAILED to create route!")

    # Try without distance check
    print("\n  Testing with 100% margin...")
    # Manually test capacity with 100%
    fits_100 = weight <= vehicle.capacity_weight and volume <= vehicle.capacity_volume
    print(f"    Fits with 100%: {fits_100}")
