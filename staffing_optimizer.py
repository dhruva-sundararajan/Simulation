###############################################################
# Staffing Optimizer for Healthcare Clinic
# Tests different staffing configurations to find optimal levels
###############################################################

import SimClasses
import SimFunctions
import SimRNG
import math
from main import RunScenario

def OptimizeStaffing(load, trauma_pct, num_replications=30):
    """
    Find optimal staffing for a given load and trauma percentage
    Tests progressively lower staffing levels until service requirements are violated
    """
    print(f"\n{'='*80}")
    print(f"OPTIMIZING STAFFING FOR {load} patients/day, {trauma_pct*100:.0f}% trauma")
    print(f"{'='*80}\n")

    # Start with conservative staffing
    if load == 75:
        base_config = {
            'SignInTriage': 2,
            'Registration': 2,
            'Examination': 3,
            'Trauma': 2,
            'Treatment': 3
        }
    elif load == 150:
        base_config = {
            'SignInTriage': 3,
            'Registration': 4,
            'Examination': 6,
            'Trauma': 3,
            'Treatment': 5
        }
    else:  # 225
        base_config = {
            'SignInTriage': 4,
            'Registration': 6,
            'Examination': 9,
            'Trauma': 4,
            'Treatment': 8
        }

    best_config = base_config.copy()
    best_total_staff = sum(base_config.values())

    print(f"Testing baseline configuration (Total Staff: {best_total_staff})...")
    results = RunScenario(load, trauma_pct, base_config, num_replications)

    # Check if baseline meets requirements
    if not CheckServiceLevels(results):
        print("WARNING: Baseline configuration does not meet service requirements!")
        return base_config, results

    # Try reducing each station one at a time
    stations = ['SignInTriage', 'Registration', 'Examination', 'Trauma', 'Treatment']

    for station in stations:
        if base_config[station] > 1:  # Can't reduce below 1
            test_config = base_config.copy()
            test_config[station] -= 1
            total_staff = sum(test_config.values())

            print(f"\nTesting with reduced {station}: {test_config[station]} (Total: {total_staff})...")
            results = RunScenario(load, trauma_pct, test_config, num_replications=20)  # Fewer reps for testing

            if CheckServiceLevels(results):
                print(f"  ✓ Still meets requirements with {station} = {test_config[station]}")
                if total_staff < best_total_staff:
                    best_config = test_config.copy()
                    best_total_staff = total_staff
            else:
                print(f"  ✗ Does not meet requirements with {station} = {test_config[station]}")

    print(f"\n{'='*80}")
    print(f"OPTIMAL CONFIGURATION (Total Staff: {best_total_staff})")
    print(f"{'='*80}")
    for station, count in best_config.items():
        print(f"  {station}: {count}")

    return best_config, results

def CheckServiceLevels(results):
    """
    Check if service level requirements are met with 95% confidence
    Returns True if all requirements met, False otherwise

    results[...] is (mean, half_width, lower, upper)
    """
    # Unpack CI results
    tri_mean, tri_hw, tri_lo, tri_hi = results['SignInTriageWait']
    tra_mean, tra_hw, tra_lo, tra_hi = results['TraumaWait']
    reg_mean, reg_hw, reg_lo, reg_hi = results['RegistrationWait']
    ex_mean,  ex_hw,  ex_lo,  ex_hi  = results['ExaminationWait']
    trt_mean, trt_hw, trt_lo, trt_hi = results['TreatmentWait']

    # Hard constraints: use UPPER CI bound to ensure requirement with 95% confidence
    # (We need to be 95% confident that the true value is below the threshold)
    if tri_hi >= 2.0:
        return False

    if tra_hi >= 5.0:
        return False

    # 15–20 minute "acceptable" constraints
    # Conservative version: use upper CI here too
    if reg_hi > 20.0:
        return False
    if ex_hi > 20.0:
        return False
    if trt_hi > 20.0:
        return False

    return True

def RelaxedServiceLevelAnalysis():
    """
    Test what staffing is needed if service levels are slightly relaxed
    """
    print("\n" + "="*80)
    print("RELAXED SERVICE LEVEL ANALYSIS")
    print("="*80)
    print("\nTesting with relaxed requirements:")
    print("  - Sign-in/Triage: < 5 minutes (was 'very fast')")
    print("  - Trauma: < 8 minutes (was < 5 minutes)")
    print("  - Others: 20-25 minutes acceptable (was 15-20 minutes)")
    print("\n(Implementation requires modifying CheckServiceLevels function)")

if __name__ == "__main__":
    # Test optimization for a few key scenarios
    test_scenarios = [
        (75, 0.10),
        (150, 0.10),
        (225, 0.10),
        (225, 0.12)  # Highest load with highest trauma
    ]

    optimal_configs = {}

    for load, trauma_pct in test_scenarios:
        config, results = OptimizeStaffing(load, trauma_pct, num_replications=30)
        optimal_configs[f"{load}_{int(trauma_pct*100)}"] = config

    print("\n\n" + "="*80)
    print("OPTIMIZATION COMPLETE - SUMMARY OF OPTIMAL STAFFING")
    print("="*80)

    for scenario_key, config in optimal_configs.items():
        load, trauma = scenario_key.split('_')
        total = sum(config.values())
        print(f"\n{load} patients/day, {trauma}% trauma (Total: {total} staff):")
        for station, count in config.items():
            print(f"  {station}: {count}")

    RelaxedServiceLevelAnalysis()
