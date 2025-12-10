# Walk-in Healthcare Clinic Simulation
**ISE 5424 Fall 2025 Project**

## Overview

This discrete-event simulation models a walk-in healthcare clinic with five stations:
1. **Sign-in/Triage** - Initial assessment to route patients
2. **Registration** - Patient registration for non-trauma cases
3. **Examination** - Medical evaluation
4. **Trauma** - Stabilization for trauma patients
5. **Treatment** - Final treatment before discharge

## Patient Flow

### Non-Trauma Patients (88-92%)
Sign-in/Triage → Registration → Examination → 40% discharged, 60% to Treatment → Discharge

### Trauma Patients (8-12%)
Sign-in/Triage → Trauma → Treatment → Discharge

## Service Time Distributions

| Station | Distribution | Parameters |
|---------|-------------|------------|
| Sign-in/Triage | Exponential | Mean = 3 min |
| Registration | Lognormal | Mean = 5 min, Variance = 2 min² |
| Examination | Normal | Mean = 16 min, Variance = 3 min² |
| Trauma | Exponential | Mean = 90 min |
| Treatment (Trauma) | Lognormal | Mean = 30 min, Variance = 4 min² |
| Treatment (Non-trauma) | Lognormal | Mean = 13.3 min, Variance = 2 min² |

## Service Level Requirements

- **Sign-in/Triage**: Very fast (< 2 minutes wait)
- **Trauma**: Average wait < 5 minutes
- **Registration, Examination, Treatment**: Average wait 15-20 minutes acceptable

## Files

- **main.py** - Main simulation code
- **SimClasses.py** - Simulation framework classes
- **SimFunctions.py** - Simulation utility functions
- **SimRNG.py** - Random number generation

## Running the Simulation

```bash
python main.py
```

The simulation will run 30 replications for each scenario and output:
- Average wait times with 95% confidence intervals
- Resource utilization rates
- Service level requirement checks

## Scenarios Tested

### Patient Loads
- 75 patients/day (light)
- 150 patients/day (medium)
- 225 patients/day (heavy)

### Trauma Percentages
- 8% (low)
- 10% (medium)
- 12% (high)

Total: 9 scenarios (3 loads × 3 trauma percentages)

## Initial Staffing Levels

### 75 Patients/Day
- Sign-in/Triage: 2 staff
- Registration: 2 staff
- Examination: 3 staff
- Trauma: 2 staff
- Treatment: 3 staff

### 150 Patients/Day
- Sign-in/Triage: 3 staff
- Registration: 4 staff
- Examination: 6 staff
- Trauma: 3 staff
- Treatment: 5 staff

### 225 Patients/Day
- Sign-in/Triage: 4 staff
- Registration: 6 staff
- Examination: 9 staff
- Trauma: 4 staff
- Treatment: 8 staff

## Customizing Staffing Levels

Edit the `staffing_configs` dictionary in [main.py](main.py:449-469) to adjust staffing:

```python
staffing_configs = {
    75: {
        'SignInTriage': 2,
        'Registration': 2,
        'Examination': 3,
        'Trauma': 2,
        'Treatment': 3
    },
    # ... more configurations
}
```

## Adjusting Number of Replications

Change the `num_replications` parameter in the scenario calls (default: 30):

```python
results = RunScenario(load, trauma_pct, staffing_configs[load], num_replications=50)
```

More replications provide tighter confidence intervals but take longer to run.

## Output Interpretation

### Wait Times
All wait times are in minutes. The output shows:
- **Mean**: Average wait time across all replications
- **Half-Width**: Half the width of the 95% confidence interval
- **95% CI Lower/Upper**: Confidence interval bounds

### Utilization
Resource utilization is shown as a percentage (0-100%). High utilization (>80%) suggests the resource is a bottleneck.

### Service Level Checks
- **PASS**: Service level requirement met
- **FAIL**: Service level requirement not met (requires more staff)

## Key Implementation Details

### Random Number Streams
Each stochastic process uses a dedicated random number stream for variance reduction:
- Stream 1: Patient arrivals
- Stream 2: Triage service times
- Stream 3: Registration service times
- Stream 4: Examination service times
- Stream 5: Trauma service times
- Stream 6: Treatment service times
- Stream 7: Trauma patient determination
- Stream 8: Discharge after examination decision

### Clinic Hours
The clinic operates for 18 hours (6 AM to midnight). Arrivals stop at midnight, but patients in the system continue to be served.

### Statistics Collection
- **DTStat**: Discrete-time statistics for wait times
- **CTStat**: Continuous-time statistics for queue lengths and resource utilization

## Potential Optimizations

1. **Reduce Triage Staff**: Sign-in/Triage shows very low utilization
2. **Increase Trauma Staff**: For 12% trauma scenarios with higher loads
3. **Balance Examination/Treatment**: Adjust based on utilization rates
4. **Relaxed Service Levels**: Test slightly higher wait times to reduce costs

## Extra Credit: Non-stationary Arrivals

To implement time-varying arrival rates (non-stationary Poisson process):

1. Create arrival rate function that varies by hour
2. Replace constant `ArrivalRate` with time-dependent function
3. Use thinning algorithm or time-varying rate in arrival scheduling

Example structure:
```python
def GetArrivalRate(current_time):
    """Return arrival rate as function of time of day"""
    hour = (current_time / 60) % 24  # Convert to hour of day
    # Define rate by hour (e.g., busier during certain hours)
    if 9 <= hour < 12:  # Morning rush
        return base_rate * 1.5
    elif 14 <= hour < 17:  # Afternoon
        return base_rate * 1.3
    else:
        return base_rate
```

## Contact

For questions about the simulation, refer to the project requirements or course materials.
