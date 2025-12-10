###############################################################
# Walk-in Healthcare Clinic Simulation - EXTRA CREDIT
# Non-stationary Poisson Process for Arrivals
#
# Uses historical arrival data from ClinicCounts2025ToPost.csv
# to model time-varying arrival rates throughout the day
###############################################################

import SimClasses
import SimFunctions
import SimRNG
import math
import csv

# Import all the classes and functions from main.py
from main import (Patient, Calendar, SignInTriageResource, RegistrationResource,
                  ExaminationResource, TraumaResource, TreatmentResource,
                  SignInTriageQueue, RegistrationQueue, ExaminationQueue,
                  TraumaQueue, TreatmentQueue, SignInTriageWait, RegistrationWait,
                  ExaminationWait, TraumaWait, TreatmentWait, ProcessSignInTriage,
                  EndSignInTriage, ProcessRegistration, EndRegistration,
                  ProcessExamination, EndExamination, ProcessTrauma, EndTrauma,
                  ProcessTreatment, EndTreatment, ConfidenceInterval,
                  ArrivalStream, TriageStream, RegistrationStream, ExaminationStream,
                  TraumaStream, TreatmentStream, TraumaDecisionStream, DischargeDecisionStream)

# Global variables
TotalArrivals = 0
TraumaPatients = 0
NonTraumaPatients = 0
PatientsCompleted = 0
SimulationHours = 18
SimulationTime = SimulationHours * 60
TraumaPercentage = 0

# Arrival rate data (will be loaded from CSV)
ArrivalRatesByHour = []  # List of 18 hourly rates

def LoadArrivalData(filename='ClinicCounts2025ToPost.csv'):
    """
    Load historical arrival data from CSV and compute average arrival rates by hour
    Returns list of 18 average rates (patients per hour) for hours 0-17 (6AM-12AM)
    """
    hourly_totals = [0.0] * 18
    day_count = 0

    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        for row in reader:
            if row and row[0]:  # Check if row has data
                day_count += 1
                for hour in range(18):
                    try:
                        count = int(row[hour])
                        hourly_totals[hour] += count
                    except (ValueError, IndexError):
                        pass

    # Compute average arrivals per hour
    if day_count > 0:
        avg_rates = [total / day_count for total in hourly_totals]
    else:
        avg_rates = [10.0] * 18  # Default if file can't be read

    return avg_rates

def GetCurrentArrivalRate(current_time):
    """
    Get the arrival rate (patients per minute) for the current simulation time

    Parameters:
    - current_time: current clock time in minutes (0 to 1080)

    Returns:
    - arrival rate in patients per minute
    """
    # Determine which hour we're in (0-17 for 6AM-12AM)
    hour_index = int(current_time / 60)
    if hour_index >= 18:
        hour_index = 17  # Cap at last hour

    # Return rate in patients per minute
    return ArrivalRatesByHour[hour_index] / 60.0

def ArrivalNonStationary():
    """Handle patient arrival event with non-stationary arrival process"""
    global TotalArrivals, TraumaPatients, NonTraumaPatients

    # Create new patient
    patient = Patient()
    TotalArrivals += 1

    # Determine if trauma patient
    if SimRNG.lcgrand(TraumaDecisionStream) < TraumaPercentage:
        patient.IsTrauma = True
        TraumaPatients += 1
    else:
        patient.IsTrauma = False
        NonTraumaPatients += 1

    # Add patient to Sign-in/Triage queue
    SignInTriageQueue.Add(patient)

    # Try to start service at Sign-in/Triage
    ProcessSignInTriage()

    # Schedule next arrival only if within operating hours
    if SimClasses.Clock < SimulationTime:
        # Get current arrival rate (time-dependent)
        current_rate = GetCurrentArrivalRate(SimClasses.Clock)

        # Generate interarrival time based on current rate
        if current_rate > 0:
            interarrival_time = SimRNG.Expon(1.0 / current_rate, ArrivalStream)
        else:
            interarrival_time = 60.0  # Default to 1 hour if rate is zero

        # Don't schedule arrivals beyond closing time
        if SimClasses.Clock + interarrival_time < SimulationTime:
            SimFunctions.Schedule(Calendar, "ArrivalNS", interarrival_time)

def RunSimulationNonStationary(trauma_pct, staff_levels):
    """
    Run one replication of the simulation with non-stationary arrivals

    Parameters:
    - trauma_pct: percentage of patients that are trauma cases (0.08 to 0.12)
    - staff_levels: dict with staffing for each station
    """
    global TotalArrivals, TraumaPatients, NonTraumaPatients, PatientsCompleted
    global TraumaPercentage, ArrivalRatesByHour

    # Initialize simulation
    SimFunctions.SimFunctionsInit(Calendar)

    # Reset counters
    TotalArrivals = 0
    TraumaPatients = 0
    NonTraumaPatients = 0
    PatientsCompleted = 0

    # Set parameters
    TraumaPercentage = trauma_pct

    # Load arrival rate data
    ArrivalRatesByHour = LoadArrivalData()

    # Set staffing levels
    SignInTriageResource.SetUnits(staff_levels['SignInTriage'])
    RegistrationResource.SetUnits(staff_levels['Registration'])
    ExaminationResource.SetUnits(staff_levels['Examination'])
    TraumaResource.SetUnits(staff_levels['Trauma'])
    TreatmentResource.SetUnits(staff_levels['Treatment'])

    # Schedule first arrival
    initial_rate = ArrivalRatesByHour[0] / 60.0  # Rate for first hour
    if initial_rate > 0:
        first_arrival = SimRNG.Expon(1.0 / initial_rate, ArrivalStream)
        SimFunctions.Schedule(Calendar, "ArrivalNS", first_arrival)

    # Main event loop
    while Calendar.N() > 0:
        next_event = Calendar.Remove()
        SimClasses.Clock = next_event.EventTime

        if next_event.EventType == "ArrivalNS":
            ArrivalNonStationary()
        elif next_event.EventType == "EndSignInTriage":
            EndSignInTriage(next_event.WhichObject)
        elif next_event.EventType == "EndRegistration":
            EndRegistration(next_event.WhichObject)
        elif next_event.EventType == "EndExamination":
            EndExamination(next_event.WhichObject)
        elif next_event.EventType == "EndTrauma":
            EndTrauma(next_event.WhichObject)
        elif next_event.EventType == "EndTreatment":
            EndTreatment(next_event.WhichObject)

    # Return statistics
    return {
        'SignInTriageWait': SignInTriageWait.Mean(),
        'RegistrationWait': RegistrationWait.Mean(),
        'ExaminationWait': ExaminationWait.Mean(),
        'TraumaWait': TraumaWait.Mean(),
        'TreatmentWait': TreatmentWait.Mean(),
        'TotalArrivals': TotalArrivals,
        'TraumaPatients': TraumaPatients,
        'PatientsCompleted': PatientsCompleted,
        'SignInTriageUtil': SignInTriageResource.Mean() / staff_levels['SignInTriage'] if staff_levels['SignInTriage'] > 0 else 0,
        'RegistrationUtil': RegistrationResource.Mean() / staff_levels['Registration'] if staff_levels['Registration'] > 0 else 0,
        'ExaminationUtil': ExaminationResource.Mean() / staff_levels['Examination'] if staff_levels['Examination'] > 0 else 0,
        'TraumaUtil': TraumaResource.Mean() / staff_levels['Trauma'] if staff_levels['Trauma'] > 0 else 0,
        'TreatmentUtil': TreatmentResource.Mean() / staff_levels['Treatment'] if staff_levels['Treatment'] > 0 else 0,
        'AvgQueueSignInTriage': SignInTriageQueue.Mean(),
        'AvgQueueRegistration': RegistrationQueue.Mean(),
        'AvgQueueExamination': ExaminationQueue.Mean(),
        'AvgQueueTrauma': TraumaQueue.Mean(),
        'AvgQueueTreatment': TreatmentQueue.Mean(),
        'MaxQueueSignInTriage': SignInTriageQueue.WIP.Max,
        'MaxQueueRegistration': RegistrationQueue.WIP.Max,
        'MaxQueueExamination': ExaminationQueue.WIP.Max,
        'MaxQueueTrauma': TraumaQueue.WIP.Max,
        'MaxQueueTreatment': TreatmentQueue.WIP.Max
    }

def RunScenarioNonStationary(trauma_pct, staff_levels, num_replications=30):
    """
    Run multiple replications for a scenario with non-stationary arrivals
    """
    print(f"\n{'='*80}")
    print(f"NON-STATIONARY SCENARIO: {trauma_pct*100:.0f}% trauma")
    print(f"Arrival pattern based on historical data (time-varying rates)")
    print(f"Staffing: Triage={staff_levels['SignInTriage']}, Registration={staff_levels['Registration']}, " +
          f"Exam={staff_levels['Examination']}, Trauma={staff_levels['Trauma']}, Treatment={staff_levels['Treatment']}")
    print(f"{'='*80}")

    # Display hourly arrival rates
    rates = LoadArrivalData()
    print("\nAverage arrival rates by hour:")
    hours = ['6-7AM', '7-8AM', '8-9AM', '9-10AM', '10-11AM', '11AM-12PM',
             '12-1PM', '1-2PM', '2-3PM', '3-4PM', '4-5PM', '5-6PM',
             '6-7PM', '7-8PM', '8-9PM', '9-10PM', '10-11PM', '11PM-12AM']

    for i, (hour, rate) in enumerate(zip(hours, rates)):
        print(f"  {hour}: {rate:.1f} patients/hour", end='')
        if (i + 1) % 3 == 0:
            print()  # New line every 3 hours

    total_expected = sum(rates)
    print(f"\nTotal expected arrivals per day: {total_expected:.1f} patients")

    # Store results from each replication
    results = {
        'SignInTriageWait': [],
        'RegistrationWait': [],
        'ExaminationWait': [],
        'TraumaWait': [],
        'TreatmentWait': [],
        'TotalArrivals': [],
        'SignInTriageUtil': [],
        'RegistrationUtil': [],
        'ExaminationUtil': [],
        'TraumaUtil': [],
        'TreatmentUtil': [],
        'MaxQueueSignInTriage': [],
        'MaxQueueRegistration': [],
        'MaxQueueExamination': [],
        'MaxQueueTrauma': [],
        'MaxQueueTreatment': []
    }

    # Run replications
    for _ in range(num_replications):
        rep_results = RunSimulationNonStationary(trauma_pct, staff_levels)

        for key in results.keys():
            results[key].append(rep_results[key])

    # Compute confidence intervals
    print(f"\nResults from {num_replications} replications:\n")
    print(f"{'Metric':<30} {'Mean':>10} {'Half-Width':>12} {'95% CI Lower':>14} {'95% CI Upper':>14}")
    print(f"{'-'*80}")

    ci_results = {}
    for key in ['SignInTriageWait', 'RegistrationWait', 'ExaminationWait', 'TraumaWait', 'TreatmentWait']:
        mean, hw, lower, upper = ConfidenceInterval(results[key])
        ci_results[key] = (mean, hw, lower, upper)
        metric_name = key.replace('Wait', ' Wait Time (min)')
        print(f"{metric_name:<30} {mean:>10.2f} {hw:>12.2f} {lower:>14.2f} {upper:>14.2f}")

    print(f"\n{'Utilization':<30}")
    for key in ['SignInTriageUtil', 'RegistrationUtil', 'ExaminationUtil', 'TraumaUtil', 'TreatmentUtil']:
        mean, hw, lower, upper = ConfidenceInterval(results[key])
        ci_results[key] = (mean, hw, lower, upper)
        metric_name = key.replace('Util', ' Utilization')
        print(f"{metric_name:<30} {mean:>10.2%} {hw:>12.2%} {lower:>14.2%} {upper:>14.2%}")

    print(f"\n{'Maximum Queue Lengths':<30}")
    for key in ['MaxQueueSignInTriage', 'MaxQueueRegistration', 'MaxQueueExamination', 'MaxQueueTrauma', 'MaxQueueTreatment']:
        mean, hw, lower, upper = ConfidenceInterval(results[key])
        metric_name = key.replace('MaxQueue', ' Max Queue')
        print(f"{metric_name:<30} {mean:>10.1f} {hw:>12.2f} {lower:>14.2f} {upper:>14.2f}")

    mean, hw, lower, upper = ConfidenceInterval(results['TotalArrivals'])
    print(f"\n{'Total Arrivals':<30} {mean:>10.1f} {hw:>12.2f} {lower:>14.2f} {upper:>14.2f}")

    # Check service level requirements
    # Unpack CI results for readability
    tri_mean, tri_hw, tri_lo, tri_hi = ci_results['SignInTriageWait']
    tra_mean, tra_hw, tra_lo, tra_hi = ci_results['TraumaWait']
    reg_mean, reg_hw, reg_lo, reg_hi = ci_results['RegistrationWait']
    ex_mean,  ex_hw,  ex_lo,  ex_hi  = ci_results['ExaminationWait']
    trt_mean, trt_hw, trt_lo, trt_hi = ci_results['TreatmentWait']

    print(f"\n{'Service Level Requirements Check:'}")
    # HARD constraints → use UPPER 95% CI bound to ensure requirement with 95% confidence
    print(f"{'  Sign-in/Triage (very fast):':<40} {'PASS' if tri_hi < 2.0 else 'FAIL'}")
    print(f"{'  Trauma Wait (<5 min):':<40} {'PASS' if tra_hi < 5.0 else 'FAIL'}")
    # Other areas: "15–20 minutes acceptable" - use upper CI bound (conservative)
    print(f"{'  Registration (15-20 min acceptable):':<40} {'PASS' if reg_hi <= 20.0 else 'FAIL'}")
    print(f"{'  Examination (15-20 min acceptable):':<40} {'PASS' if ex_hi <= 20.0 else 'FAIL'}")
    print(f"{'  Treatment (15-20 min acceptable):':<40} {'PASS' if trt_hi <= 20.0 else 'FAIL'}")

    return ci_results

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WALK-IN HEALTHCARE CLINIC SIMULATION - NON-STATIONARY ARRIVALS (EXTRA CREDIT)")
    print("ISE 5424 Fall 2025 Project")
    print("="*80)

    # Test with trauma percentages using the historical arrival pattern
    trauma_percentages = [0.08, 0.10, 0.12]

    # Use staffing based on the average daily arrivals from historical data
    # The historical data shows average of ~220 patients per day
    staffing_config = {
        'SignInTriage': 4,
        'Registration': 6,
        'Examination': 9,
        'Trauma': 4,
        'Treatment': 8
    }

    print("\nUsing staffing configuration for high-load scenario (~220 patients/day):")
    for station, count in staffing_config.items():
        print(f"  {station}: {count}")

    all_results = {}

    for trauma_pct in trauma_percentages:
        scenario_key = f"NS_{int(trauma_pct*100)}"
        results = RunScenarioNonStationary(trauma_pct, staffing_config, num_replications=30)
        all_results[scenario_key] = results

    print("\n" + "="*80)
    print("NON-STATIONARY SIMULATION COMPLETE")
    print("="*80)