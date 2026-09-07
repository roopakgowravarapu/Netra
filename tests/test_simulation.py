"""Unit tests for Telemedicine Operational Queue Simulation."""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.simulation.screening_sim import SimParameters, run_operational_simulation


def test_simulation_parameter_validation():
    """Verify parameter validation."""
    params = SimParameters(arrival_rate_per_hr=-5.0)
    with pytest.raises(ValueError):
        params.validate()


def test_simulation_workload_scenarios():
    """Verify simulation execution for Low, Medium, High workloads."""
    for rate in [10.0, 30.0, 60.0]:
        params = SimParameters(arrival_rate_per_hr=rate)
        results = run_operational_simulation(params)

        assert results["patients_arrived"] > 0
        assert results["throughput_pts_per_hr"] >= 0.0
        assert 0.0 <= results["ai_processing_utilization_pct"] <= 100.0
        assert 0.0 <= results["specialist_utilization_pct"] <= 100.0
