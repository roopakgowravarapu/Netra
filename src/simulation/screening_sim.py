"""Discrete-Event Operational Queue Simulation for Netra Telemedicine Centers.

Simulates patient arrival, image capture, Netra AI inference, report synthesis, and specialist review.
"""

from dataclasses import dataclass, field
import heapq
from typing import Dict, List, Tuple, Any


@dataclass
class SimParameters:
    arrival_rate_per_hr: float  # e.g., 10, 30, 60
    acquisition_time_min: float = 3.0
    ai_processing_time_min: float = 0.5  # Measured Netra pipeline inference (~30s)
    report_gen_time_min: float = 0.2
    specialist_review_time_min: float = 5.0
    num_technicians: int = 2
    num_ai_workers: int = 1
    num_specialists: int = 1
    simulation_duration_hrs: float = 8.0  # 8-hour workday shift

    def validate(self):
        if self.arrival_rate_per_hr <= 0:
            raise ValueError("Arrival rate must be positive.")
        if self.simulation_duration_hrs <= 0:
            raise ValueError("Simulation duration must be positive.")


def run_operational_simulation(params: SimParameters) -> Dict[str, Any]:
    """Runs discrete-event queue simulation for the given parameters."""
    params.validate()

    np_rng = 42
    import numpy as np
    rng = np.random.RandomState(42)

    total_sim_time_min = params.simulation_duration_hrs * 60.0
    mean_interarrival_min = 60.0 / params.arrival_rate_per_hr

    # Event Queue: (time, event_type, patient_id)
    # Event Types: ARRIVAL, ACQ_COMPLETE, AI_COMPLETE, SPECIALIST_COMPLETE
    events = []
    patient_id = 0
    t = 0.0

    # Schedule arrivals
    while t < total_sim_time_min:
        interarrival = rng.exponential(mean_interarrival_min)
        t += interarrival
        if t < total_sim_time_min:
            patient_id += 1
            heapq.heappush(events, (t, "ARRIVAL", patient_id))

    total_patients_arrived = patient_id

    # Resources & Queues
    acq_free = params.num_technicians
    ai_free = params.num_ai_workers
    specialist_free = params.num_specialists

    acq_queue = []
    ai_queue = []
    specialist_queue = []

    patient_arrival_time = {}
    patient_wait_times = []

    acq_busy_time = 0.0
    ai_busy_time = 0.0
    specialist_busy_time = 0.0

    acq_queue_lengths = []
    specialist_queue_lengths = []

    processed_patients = 0
    images_processed = 0

    while events:
        now, etype, pid = heapq.heappop(events)

        if etype == "ARRIVAL":
            patient_arrival_time[pid] = now
            images_processed += 1
            if acq_free > 0:
                acq_free -= 1
                service_time = rng.exponential(params.acquisition_time_min)
                acq_busy_time += service_time
                heapq.heappush(events, (now + service_time, "ACQ_COMPLETE", pid))
            else:
                acq_queue.append(pid)
                acq_queue_lengths.append(len(acq_queue))

        elif etype == "ACQ_COMPLETE":
            if acq_queue:
                next_pid = acq_queue.pop(0)
                service_time = rng.exponential(params.acquisition_time_min)
                acq_busy_time += service_time
                heapq.heappush(events, (now + service_time, "ACQ_COMPLETE", next_pid))
            else:
                acq_free += 1

            if ai_free > 0:
                ai_free -= 1
                service_time = rng.exponential(params.ai_processing_time_min + params.report_gen_time_min)
                ai_busy_time += service_time
                heapq.heappush(events, (now + service_time, "AI_COMPLETE", pid))
            else:
                ai_queue.append(pid)

        elif etype == "AI_COMPLETE":
            if ai_queue:
                next_pid = ai_queue.pop(0)
                service_time = rng.exponential(params.ai_processing_time_min + params.report_gen_time_min)
                ai_busy_time += service_time
                heapq.heappush(events, (now + service_time, "AI_COMPLETE", next_pid))
            else:
                ai_free += 1

            if specialist_free > 0:
                specialist_free -= 1
                service_time = rng.exponential(params.specialist_review_time_min)
                specialist_busy_time += service_time
                heapq.heappush(events, (now + service_time, "SPECIALIST_COMPLETE", pid))
            else:
                specialist_queue.append(pid)
                specialist_queue_lengths.append(len(specialist_queue))

        elif etype == "SPECIALIST_COMPLETE":
            processed_patients += 1
            wait = now - patient_arrival_time[pid]
            patient_wait_times.append(wait)

            if specialist_queue:
                next_pid = specialist_queue.pop(0)
                service_time = rng.exponential(params.specialist_review_time_min)
                specialist_busy_time += service_time
                heapq.heappush(events, (now + service_time, "SPECIALIST_COMPLETE", next_pid))
            else:
                specialist_free += 1

    avg_wait = float(np.mean(patient_wait_times)) if patient_wait_times else 0.0
    throughput = float(processed_patients / params.simulation_duration_hrs)
    ai_utilization = min(1.0, float(ai_busy_time / (total_sim_time_min * params.num_ai_workers)))
    specialist_utilization = min(1.0, float(specialist_busy_time / (total_sim_time_min * params.num_specialists)))
    avg_spec_queue = float(np.mean(specialist_queue_lengths)) if specialist_queue_lengths else 0.0

    return {
        "arrival_rate_per_hr": params.arrival_rate_per_hr,
        "patients_arrived": total_patients_arrived,
        "patients_processed": processed_patients,
        "images_processed": images_processed,
        "throughput_pts_per_hr": round(throughput, 2),
        "avg_waiting_time_min": round(avg_wait, 2),
        "avg_specialist_queue_len": round(avg_spec_queue, 2),
        "ai_processing_utilization_pct": round(ai_utilization * 100, 2),
        "specialist_utilization_pct": round(specialist_utilization * 100, 2),
    }
