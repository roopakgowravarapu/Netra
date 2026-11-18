"""Annual 100,000+ Patient Screening Operational Simulation Runner.

Simulates and quantifies the operational parameters for population-scale screening:
- 100,000+ annual patients across rural screening centers
- Image acquisition throughput
- Rural bandwidth transmission constraints (5-15 MB per scan)
- Netra AI processing latency (~0.65s)
- Specialist review queue length and capacity
- Waiting time & resource bottleneck analysis
"""

import json
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def simulate_annual_100k_operations(
    annual_patients: int = 100000,
    operating_days: int = 250,
    daily_hours: int = 8,
    screening_stations: int = 20,
    image_size_mb: float = 8.0,
    bandwidth_mbps: float = 4.0,
    ai_proc_time_sec: float = 0.65,
    explain_time_sec: float = 0.25,
    referable_dr_rate: float = 0.22,
    reviewers_count: int = 4,
    specialist_review_min: float = 4.0,
) -> Dict[str, Any]:
    """Runs high-scale discrete queuing simulation based on M/M/k Erlang-C queueing theory."""
    total_hours = operating_days * daily_hours
    hourly_arrival_rate = annual_patients / total_hours
    station_arrival_rate = hourly_arrival_rate / screening_stations

    # Bandwidth transmission
    transfer_time_sec = (image_size_mb * 8.0) / bandwidth_mbps
    ai_throughput_per_hr = 3600.0 / (ai_proc_time_sec + explain_time_sec)

    # Specialist Queuing
    referable_arrival_rate_per_hr = hourly_arrival_rate * referable_dr_rate
    reviewer_service_rate_per_hr = 60.0 / specialist_review_min
    total_specialist_capacity = reviewers_count * reviewer_service_rate_per_hr

    rho = referable_arrival_rate_per_hr / total_specialist_capacity

    if rho < 1.0:
        # Erlang-C model approximation
        k = reviewers_count
        r = referable_arrival_rate_per_hr / reviewer_service_rate_per_hr
        import math
        sum_terms = sum((r ** n) / math.factorial(n) for n in range(k))
        c_term = (r ** k) / (math.factorial(k) * (1.0 - rho))
        p0 = 1.0 / (sum_terms + c_term)
        erlang_c_prob = c_term * p0
        avg_queue_len = (erlang_c_prob * rho) / (1.0 - rho)
        avg_wait_time_min = (avg_queue_len / referable_arrival_rate_per_hr) * 60.0
        status = "STABLE"
    else:
        avg_queue_len = 50.0 + (rho - 1.0) * 100.0
        avg_wait_time_min = 120.0 * rho
        status = "BOTTLENECK_IDENTIFIED: SPECIALIST_CAPACITY_EXCEEDED"

    network_bottleneck = (
        "HIGH: Rural upload latency dominates turnaround time. Recommend edge image compression."
        if transfer_time_sec > 15.0
        else "OPTIMAL: Transmission latency within target bounds."
    )

    specialist_recommendation = (
        f"Ophthalmologist utilization is high ({rho*100:.1f}%). Add additional reviewer to maintain <15min turnaround."
        if rho > 0.85
        else f"Specialist capacity is balanced ({rho*100:.1f}% utilization). Response times within clinical targets."
    )

    results = {
        "annual_patients_simulated": annual_patients,
        "operating_days": operating_days,
        "screening_stations": screening_stations,
        "system_status": status,
        "hourly_screening_rate": round(hourly_arrival_rate, 1),
        "station_screening_rate": round(station_arrival_rate, 2),
        "network_transfer_time_sec": round(transfer_time_sec, 2),
        "ai_throughput_capacity_per_hour": round(ai_throughput_per_hr, 0),
        "referable_cases_per_hour": round(referable_arrival_rate_per_hr, 1),
        "specialist_reviewers_count": reviewers_count,
        "specialist_utilization_pct": round(rho * 100, 1),
        "average_queue_length_cases": round(avg_queue_len, 2),
        "average_patient_wait_time_min": round(avg_wait_time_min, 1),
        "bottlenecks": {
            "network_latency": network_bottleneck,
            "specialist_review": specialist_recommendation,
        },
    }

    out_dir = ROOT_DIR / "outputs" / "simulation"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "annual_100k_simulink_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    res = simulate_annual_100k_operations()
    print("Annual 100k Simulink Simulation Complete:")
    print(json.dumps(res, indent=2))
