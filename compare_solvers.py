#!/usr/bin/env python3
"""Compare performance of different solver versions"""
from robin_logistics import LogisticsEnvironment
import importlib
import sys


def test_solver(solver_module_name: str, solver_name: str):
    """Test a solver and return stats"""
    print(f"\n{'='*70}")
    print(f"Testing: {solver_name}")
    print(f"{'='*70}\n")

    # Import solver
    solver_module = importlib.import_module(solver_module_name)
    solver_func = solver_module.solver

    # Create environment
    env = LogisticsEnvironment()

    # Run solver
    print("Running solver...")
    result = solver_func(env)
    print(f"✓ Routes created: {len(result['routes'])}")

    # Validate
    print("\nValidating solution...")
    is_valid, msg, details = env.validate_solution_complete(result)

    if not is_valid:
        print(f"✗ INVALID: {msg}")
        return None

    print(f"✓ Valid solution")

    # Execute
    print("\nExecuting solution...")
    success, exec_msg = env.execute_solution(result)
    print(f"Execution result: {exec_msg}")

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

    # Display results
    print(f"\n{'='*70}")
    print(f"RESULTS: {solver_name}")
    print(f"{'='*70}")
    print(f"Orders Fulfilled:  {fulfilled}/50 ({100*fulfilled/50:.1f}%)")
    print(f"Total Cost:        ${stats.get('total_cost', 0):,.2f}")
    print(f"Total Distance:    {stats.get('total_distance', 0):,.2f} km")
    print(f"Vehicles Used:     {len(result['routes'])}/12")
    print(f"Routes Executed:   {exec_msg}")

    if unfulfilled:
        print(f"\nUnfulfilled Orders ({len(unfulfilled)}): {unfulfilled[:5]}{'...' if len(unfulfilled) > 5 else ''}")

    return {
        'name': solver_name,
        'fulfillment': fulfilled,
        'fulfillment_pct': 100 * fulfilled / 50,
        'cost': stats.get('total_cost', 0),
        'distance': stats.get('total_distance', 0),
        'routes': len(result['routes']),
        'unfulfilled': len(unfulfilled)
    }


def main():
    """Compare all solver versions"""
    solvers = [
        ('VibeCoders_solver_1', 'Solver v1 (Current - 78%)'),
        ('VibeCoders_solver_4', 'Solver v4 (Balanced Enhancement)'),
    ]

    results = []

    for module_name, display_name in solvers:
        try:
            result = test_solver(module_name, display_name)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n✗ ERROR testing {display_name}: {e}")
            import traceback
            traceback.print_exc()

    # Comparison summary
    if len(results) >= 2:
        print(f"\n{'='*70}")
        print("COMPARISON SUMMARY")
        print(f"{'='*70}\n")

        print(f"{'Metric':<20} {'v1':<20} {'v4':<20} {'Delta':<15}")
        print(f"{'-'*70}")

        v1 = results[0]
        v4 = results[1]

        print(f"{'Fulfillment':<20} {v1['fulfillment']}/50 ({v1['fulfillment_pct']:.1f}%){'':<5} "
              f"{v4['fulfillment']}/50 ({v4['fulfillment_pct']:.1f}%){'':<5} "
              f"{'+' if v4['fulfillment'] > v1['fulfillment'] else ''}{v4['fulfillment'] - v1['fulfillment']} orders")

        print(f"{'Cost':<20} ${v1['cost']:,.2f}{'':<10} "
              f"${v4['cost']:,.2f}{'':<10} "
              f"{'↓' if v4['cost'] < v1['cost'] else '↑'} ${abs(v4['cost'] - v1['cost']):,.2f}")

        print(f"{'Distance':<20} {v1['distance']:.2f} km{'':<10} "
              f"{v4['distance']:.2f} km{'':<10} "
              f"{'↓' if v4['distance'] < v1['distance'] else '↑'} {abs(v4['distance'] - v1['distance']):.2f} km")

        print(f"{'Routes Used':<20} {v1['routes']}/12{'':<14} "
              f"{v4['routes']}/12{'':<14} "
              f"{'+' if v4['routes'] > v1['routes'] else ''}{v4['routes'] - v1['routes']}")

        print(f"\n{'='*70}")

        # Winner
        if v4['fulfillment'] > v1['fulfillment']:
            print(f"🏆 WINNER: Solver v4 with {v4['fulfillment_pct']:.1f}% fulfillment!")
            print(f"   Improvement: +{v4['fulfillment'] - v1['fulfillment']} orders (+{v4['fulfillment_pct'] - v1['fulfillment_pct']:.1f}%)")
        elif v4['fulfillment'] == v1['fulfillment']:
            if v4['cost'] < v1['cost']:
                print(f"🏆 WINNER: Solver v4 with same fulfillment but lower cost!")
                print(f"   Cost savings: ${v1['cost'] - v4['cost']:,.2f}")
            else:
                print(f"⚖️  TIE: Both solvers achieve {v1['fulfillment_pct']:.1f}% fulfillment")
        else:
            print(f"⚠️  Solver v1 still better with {v1['fulfillment_pct']:.1f}% fulfillment")

        print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
