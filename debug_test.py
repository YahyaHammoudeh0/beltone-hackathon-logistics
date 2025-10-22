#!/usr/bin/env python3
"""Debug test with execution"""
from robin_logistics import LogisticsEnvironment
from VibeCoders_solver_1 import solver

if __name__ == '__main__':
    env = LogisticsEnvironment()
    result = solver(env)

    print(f"Routes created: {len(result['routes'])}\n")

    # Validate
    is_valid, msg, details = env.validate_solution_complete(result)
    print(f"Validation: {is_valid} - {msg}\n")

    if is_valid:
        # Check route structure
        print("Route Summary:")
        for i, route in enumerate(result['routes'], 1):
            vehicle_id = route['vehicle_id']
            num_steps = len(route['steps'])

            # Count deliveries
            deliveries = 0
            orders = set()
            for step in route['steps']:
                deliveries += len(step.get('deliveries', []))
                for d in step.get('deliveries', []):
                    orders.add(d['order_id'])

            print(f"  Route {i}: {vehicle_id} - {num_steps} steps, {len(orders)} orders, {deliveries} deliveries")

        # Execute
        print("\n" + "="*60)
        print("Executing solution...")
        print("="*60)
        success, exec_msg = env.execute_solution(result)
        print(f"\nExecution Result: {success}")
        print(f"Message: {exec_msg}\n")

        # Check individual order fulfillment
        all_orders = env.get_all_order_ids()
        fulfilled_count = 0
        unfulfilled = []

        for order_id in all_orders:
            status = env.get_order_fulfillment_status(order_id)
            if status == 'fulfilled':
                fulfilled_count += 1
            else:
                unfulfilled.append(order_id)

        print(f"Orders Fulfilled: {fulfilled_count}/{len(all_orders)}")
        print(f"Fulfillment Rate: {fulfilled_count/len(all_orders)*100:.1f}%")

        if unfulfilled:
            print(f"\nUnfulfilled orders ({len(unfulfilled)}): {unfulfilled[:5]}{'...' if len(unfulfilled) > 5 else ''}")

        # Re-validate after execution to get updated stats
        is_valid2, msg2, details2 = env.validate_solution_complete(result)
        stats = env.get_solution_statistics(result, details2)
        print(f"\nTotal Cost: ${stats.get('total_cost', 0):,.2f}")
        print(f"Total Distance: {stats.get('total_distance', 0):,.2f} km")
