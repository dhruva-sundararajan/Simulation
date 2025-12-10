###############################################################
# Comparison Analysis: Stationary vs Non-Stationary Arrivals
# Demonstrates the impact of time-varying arrival rates
###############################################################

import sys
from datetime import datetime

def RunComparisonAnalysis():
    """
    Run both stationary and non-stationary simulations and compare results
    """
    output_filename = f"comparison_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    original_stdout = sys.stdout

    with open(output_filename, 'w') as f:
        sys.stdout = f

        print("="*80)
        print("STATIONARY VS NON-STATIONARY ARRIVAL PROCESS COMPARISON")
        print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print()

        print("="*80)
        print("PART 1: STATIONARY POISSON PROCESS (Base Model)")
        print("="*80)
        print("\nAssumption: Constant arrival rate throughout 18-hour operating period")
        print("Testing 225 patients/day with 10% trauma\n")

        # Import and run stationary simulation
        from main import RunScenario

        staffing_stationary = {
            'SignInTriage': 4,
            'Registration': 6,
            'Examination': 9,
            'Trauma': 6,
            'Treatment': 7
        }

        print("Running stationary model...")
        results_stationary = RunScenario(225, 0.10, staffing_stationary, num_replications=30)

        print("\n" + "="*80)
        print("PART 2: NON-STATIONARY POISSON PROCESS (Extra Credit)")
        print("="*80)
        print("\nAssumption: Time-varying arrival rate based on historical data")
        print("Average ~227 patients/day with 10% trauma\n")

        # Import and run non-stationary simulation
        from main_nonstationary import RunScenarioNonStationary

        print("Running non-stationary model...")
        results_nonstationary = RunScenarioNonStationary(0.10, staffing_stationary, num_replications=30)

        print("\n" + "="*80)
        print("PART 3: COMPARISON AND ANALYSIS")
        print("="*80)

        print("\n1. AVERAGE WAIT TIMES COMPARISON")
        print("-" * 80)
        print(f"{'Station':<30} {'Stationary (min)':<20} {'Non-Stationary (min)':<20}")
        print("-" * 80)

        stations = ['SignInTriageWait', 'RegistrationWait', 'ExaminationWait', 'TraumaWait', 'TreatmentWait']
        station_names = ['Sign-in/Triage', 'Registration', 'Examination', 'Trauma', 'Treatment']

        for station, name in zip(stations, station_names):
            stat_mean = results_stationary[station][0]
            nonstat_mean = results_nonstationary[station][0]
            print(f"{name:<30} {stat_mean:>18.2f}  {nonstat_mean:>18.2f}")

        print("\n2. UTILIZATION COMPARISON")
        print("-" * 80)
        print(f"{'Station':<30} {'Stationary (%)':<20} {'Non-Stationary (%)':<20}")
        print("-" * 80)

        util_stations = ['SignInTriageUtil', 'RegistrationUtil', 'ExaminationUtil', 'TraumaUtil', 'TreatmentUtil']

        for station, name in zip(util_stations, station_names):
            stat_util = results_stationary[station][0] * 100
            nonstat_util = results_nonstationary[station][0] * 100
            print(f"{name:<30} {stat_util:>18.1f}  {nonstat_util:>18.1f}")
            
    sys.stdout = original_stdout
    print(f"\nComparison analysis complete! Results saved to: {output_filename}")
    return output_filename

if __name__ == "__main__":
    RunComparisonAnalysis()
