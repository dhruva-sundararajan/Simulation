###############################################################
# Walk-in Healthcare Clinic Simulation
# ISE 5424 Fall 2025 Project
#
# Simulates a 5-station healthcare clinic with:
# - Sign-in/Triage
# - Registration
# - Examination
# - Trauma
# - Treatment
###############################################################

import SimClasses
import SimFunctions
import SimRNG
import math

# Patient class extending Entity
class Patient(SimClasses.Entity):
    def __init__(self):
        super().__init__()
        self.IsTrauma = False
        self.TriageTime = 0.0
        self.RegistrationTime = 0.0
        self.ExaminationTime = 0.0
        self.TraumaTime = 0.0
        self.TreatmentTime = 0.0

# Global variables for simulation
Calendar = SimClasses.EventCalendar()

# Resources for each station
SignInTriageResource = SimClasses.Resource()
RegistrationResource = SimClasses.Resource()
ExaminationResource = SimClasses.Resource()
TraumaResource = SimClasses.Resource()
TreatmentResource = SimClasses.Resource()

# Queues for each station
SignInTriageQueue = SimClasses.FIFOQueue()
RegistrationQueue = SimClasses.FIFOQueue()
ExaminationQueue = SimClasses.FIFOQueue()
TraumaQueue = SimClasses.FIFOQueue()
TreatmentQueue = SimClasses.FIFOQueue()

# Wait time statistics
SignInTriageWait = SimClasses.DTStat()
RegistrationWait = SimClasses.DTStat()
ExaminationWait = SimClasses.DTStat()
TraumaWait = SimClasses.DTStat()
TreatmentWait = SimClasses.DTStat()

# Patient counters
TotalArrivals = 0
TraumaPatients = 0
NonTraumaPatients = 0
PatientsCompleted = 0

# Simulation parameters
SimulationHours = 18  # 6 AM to 12 PM (midnight)
SimulationTime = SimulationHours * 60  # in minutes
ArrivalRate = 0  # patients per minute (set based on scenario)
TraumaPercentage = 0  # percentage of trauma patients (set based on scenario)

# Random number stream assignments
ArrivalStream = 1
TriageStream = 2
RegistrationStream = 3
ExaminationStream = 4
TraumaStream = 5
TreatmentStream = 6
TraumaDecisionStream = 7
DischargeDecisionStream = 8

def Arrival():
    """Handle patient arrival event"""
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
        interarrival_time = SimRNG.Expon(1.0 / ArrivalRate, ArrivalStream)
        SimFunctions.Schedule(Calendar, "Arrival", interarrival_time)

def ProcessSignInTriage():
    """Process patients in Sign-in/Triage queue"""
    while SignInTriageQueue.NumQueue() > 0 and SignInTriageResource.Seize(1):
        patient = SignInTriageQueue.Remove()

        # Record wait time
        wait_time = SimClasses.Clock - patient.CreateTime
        SignInTriageWait.Record(wait_time)

        # Generate service time (Exponential with mean 3 minutes)
        service_time = SimRNG.Expon(3.0, TriageStream)

        # Schedule end of triage
        SimFunctions.SchedulePlus(Calendar, "EndSignInTriage", service_time, patient)

def EndSignInTriage(patient):
    """Complete Sign-in/Triage and route patient"""
    SignInTriageResource.Free(1)
    patient.TriageTime = SimClasses.Clock

    # Route based on trauma status
    if patient.IsTrauma:
        # Send to Trauma
        TraumaQueue.Add(patient)
        ProcessTrauma()
    else:
        # Send to Registration
        RegistrationQueue.Add(patient)
        ProcessRegistration()

    # Check if more patients waiting at triage
    ProcessSignInTriage()

def ProcessRegistration():
    """Process patients in Registration queue"""
    while RegistrationQueue.NumQueue() > 0 and RegistrationResource.Seize(1):
        patient = RegistrationQueue.Remove()

        # Record wait time
        wait_time = SimClasses.Clock - patient.TriageTime
        RegistrationWait.Record(wait_time)

        # Generate service time (Lognormal with mean 5, variance 2)
        service_time = SimRNG.Lognormal(5.0, 2.0, RegistrationStream)

        # Schedule end of registration
        SimFunctions.SchedulePlus(Calendar, "EndRegistration", service_time, patient)

def EndRegistration(patient):
    """Complete Registration and send to Examination"""
    RegistrationResource.Free(1)
    patient.RegistrationTime = SimClasses.Clock

    # Send to Examination
    ExaminationQueue.Add(patient)
    ProcessExamination()

    # Check if more patients waiting at registration
    ProcessRegistration()

def ProcessExamination():
    """Process patients in Examination queue"""
    while ExaminationQueue.NumQueue() > 0 and ExaminationResource.Seize(1):
        patient = ExaminationQueue.Remove()

        # Record wait time
        wait_time = SimClasses.Clock - patient.RegistrationTime
        ExaminationWait.Record(wait_time)

        # Generate service time (Normal with mean 16, variance 3)
        service_time = SimRNG.Normal(16.0, 3.0, ExaminationStream)
        # Ensure non-negative service time
        if service_time < 0:
            service_time = 0.1

        # Schedule end of examination
        SimFunctions.SchedulePlus(Calendar, "EndExamination", service_time, patient)

def EndExamination(patient):
    """Complete Examination and route patient"""
    global PatientsCompleted

    ExaminationResource.Free(1)
    patient.ExaminationTime = SimClasses.Clock

    # 40% discharged immediately, 60% go to treatment
    if SimRNG.lcgrand(DischargeDecisionStream) < 0.40:
        # Patient discharged
        PatientsCompleted += 1
    else:
        # Send to Treatment
        TreatmentQueue.Add(patient)
        ProcessTreatment()

    # Check if more patients waiting at examination
    ProcessExamination()

def ProcessTrauma():
    """Process patients in Trauma queue"""
    while TraumaQueue.NumQueue() > 0 and TraumaResource.Seize(1):
        patient = TraumaQueue.Remove()

        # Record wait time
        wait_time = SimClasses.Clock - patient.TriageTime
        TraumaWait.Record(wait_time)

        # Generate service time (Exponential with mean 90 minutes)
        service_time = SimRNG.Expon(90.0, TraumaStream)

        # Schedule end of trauma
        SimFunctions.SchedulePlus(Calendar, "EndTrauma", service_time, patient)

def EndTrauma(patient):
    """Complete Trauma and send to Treatment"""
    TraumaResource.Free(1)
    patient.TraumaTime = SimClasses.Clock

    # Send to Treatment
    TreatmentQueue.Add(patient)
    ProcessTreatment()

    # Check if more patients waiting at trauma
    ProcessTrauma()

def ProcessTreatment():
    """Process patients in Treatment queue"""
    while TreatmentQueue.NumQueue() > 0 and TreatmentResource.Seize(1):
        patient = TreatmentQueue.Remove()

        # Record wait time based on where patient came from
        if patient.IsTrauma:
            wait_time = SimClasses.Clock - patient.TraumaTime
        else:
            wait_time = SimClasses.Clock - patient.ExaminationTime
        TreatmentWait.Record(wait_time)

        # Generate service time based on trauma status
        if patient.IsTrauma:
            # Lognormal with mean 30, variance 4
            service_time = SimRNG.Lognormal(30.0, 4.0, TreatmentStream)
        else:
            # Lognormal with mean 13.3, variance 2
            service_time = SimRNG.Lognormal(13.3, 2.0, TreatmentStream)

        # Schedule end of treatment
        SimFunctions.SchedulePlus(Calendar, "EndTreatment", service_time, patient)

def EndTreatment(patient):
    """Complete Treatment and discharge patient"""
    global PatientsCompleted

    TreatmentResource.Free(1)
    patient.TreatmentTime = SimClasses.Clock

    # Patient discharged
    PatientsCompleted += 1

    # Check if more patients waiting at treatment
    ProcessTreatment()

def RunSimulation(avg_patients_per_day, trauma_pct, staff_levels):
    """
    Run one replication of the simulation

    Parameters:
    - avg_patients_per_day: average number of patients arriving per day
    - trauma_pct: percentage of patients that are trauma cases (0.08 to 0.12)
    - staff_levels: dict with staffing for each station
    """
    global TotalArrivals, TraumaPatients, NonTraumaPatients, PatientsCompleted
    global ArrivalRate, TraumaPercentage

    # Initialize simulation
    SimFunctions.SimFunctionsInit(Calendar)

    # Reset counters
    TotalArrivals = 0
    TraumaPatients = 0
    NonTraumaPatients = 0
    PatientsCompleted = 0

    # Set parameters
    ArrivalRate = avg_patients_per_day / (SimulationHours * 60)  # patients per minute
    TraumaPercentage = trauma_pct

    # Set staffing levels
    SignInTriageResource.SetUnits(staff_levels['SignInTriage'])
    RegistrationResource.SetUnits(staff_levels['Registration'])
    ExaminationResource.SetUnits(staff_levels['Examination'])
    TraumaResource.SetUnits(staff_levels['Trauma'])
    TreatmentResource.SetUnits(staff_levels['Treatment'])

    # Schedule first arrival
    first_arrival = SimRNG.Expon(1.0 / ArrivalRate, ArrivalStream)
    SimFunctions.Schedule(Calendar, "Arrival", first_arrival)

    # Main event loop
    while Calendar.N() > 0:
        next_event = Calendar.Remove()
        SimClasses.Clock = next_event.EventTime

        if next_event.EventType == "Arrival":
            Arrival()
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
        'AvgQueueTreatment': TreatmentQueue.Mean()
    }

def ConfidenceInterval(data, confidence=0.95):
    """
    Calculate confidence interval for a list of observations
    Returns (mean, half_width, lower, upper)
    """
    n = len(data)
    if n < 2:
        return (data[0] if n == 1 else 0, 0, 0, 0)

    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    std_dev = math.sqrt(variance)

    # t-value for 95% confidence with n-1 degrees of freedom
    # Using approximation for large n
    if confidence == 0.95:
        if n <= 30:
            t_values = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
                       7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228,
                       12: 2.201, 13: 2.179, 14: 2.160, 15: 2.145, 16: 2.131,
                       17: 2.120, 18: 2.110, 19: 2.101, 20: 2.093, 21: 2.086,
                       22: 2.080, 23: 2.074, 24: 2.069, 25: 2.064, 26: 2.060,
                       27: 2.056, 28: 2.052, 29: 2.048, 30: 2.045}
            t = t_values.get(n, 2.045)
        else:
            t = 1.96  # For large n, use normal approximation
    else:
        t = 1.96

    half_width = t * std_dev / math.sqrt(n)
    return (mean, half_width, mean - half_width, mean + half_width)

def RunScenario(avg_patients_per_day, trauma_pct, staff_levels, num_replications=30):
    """
    Run multiple replications for a scenario and compute confidence intervals
    """
    print(f"\n{'='*80}")
    print(f"SCENARIO: {avg_patients_per_day} patients/day, {trauma_pct*100:.0f}% trauma")
    print(f"Staffing: Triage={staff_levels['SignInTriage']}, Registration={staff_levels['Registration']}, " +
          f"Exam={staff_levels['Examination']}, Trauma={staff_levels['Trauma']}, Treatment={staff_levels['Treatment']}")
    print(f"{'='*80}")

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
        'TreatmentUtil': []
    }

    # Run replications
    for _ in range(num_replications):
        rep_results = RunSimulation(avg_patients_per_day, trauma_pct, staff_levels)

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

    mean, hw, lower, upper = ConfidenceInterval(results['TotalArrivals'])
    print(f"\n{'Total Arrivals':<30} {mean:>10.1f} {hw:>12.2f} {lower:>14.2f} {upper:>14.2f}")

    # Check service level requirements
    print(f"\n{'Service Level Requirements Check:'}")
    print(f"{'  Sign-in/Triage (very fast):':<40} {'PASS' if ci_results['SignInTriageWait'][2] < 2 else 'FAIL'}")
    print(f"{'  Trauma Wait (<5 min):':<40} {'PASS' if ci_results['TraumaWait'][2] < 5 else 'FAIL'}")
    print(f"{'  Registration (15-20 min acceptable):':<40} {'PASS' if ci_results['RegistrationWait'][0] <= 20 else 'FAIL'}")
    print(f"{'  Examination (15-20 min acceptable):':<40} {'PASS' if ci_results['ExaminationWait'][0] <= 20 else 'FAIL'}")
    print(f"{'  Treatment (15-20 min acceptable):':<40} {'PASS' if ci_results['TreatmentWait'][0] <= 20 else 'FAIL'}")

    return ci_results

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WALK-IN HEALTHCARE CLINIC SIMULATION")
    print("ISE 5424 Fall 2025 Project")
    print("="*80)

    # Define scenarios to test
    patient_loads = [75, 150, 225]  # patients per day
    trauma_percentages = [0.08, 0.10, 0.12]  # 8%, 10%, 12%

    # Initial staffing levels (to be adjusted based on results)
    # These are starting points and should be optimized
    staffing_configs = {
        75: {
            'SignInTriage': 2,
            'Registration': 2,
            'Examination': 3,
            'Trauma': 2,
            'Treatment': 3
        },
        150: {
            'SignInTriage': 3,
            'Registration': 4,
            'Examination': 6,
            'Trauma': 3,
            'Treatment': 5
        },
        225: {
            'SignInTriage': 4,
            'Registration': 6,
            'Examination': 9,
            'Trauma': 4,
            'Treatment': 8
        }
    }

    # Run scenarios
    all_results = {}

    for load in patient_loads:
        for trauma_pct in trauma_percentages:
            scenario_key = f"{load}_{int(trauma_pct*100)}"
            results = RunScenario(load, trauma_pct, staffing_configs[load], num_replications=30)
            all_results[scenario_key] = results

    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    print("\nReview the results above to determine optimal staffing levels.")
    print("Adjust staffing configurations in the code and re-run as needed.")
