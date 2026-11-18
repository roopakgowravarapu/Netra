"""Automated Unit & Workflow Tests for Netra DR-Grade Clinical Routing and Specialist Review."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
from backend.app.services.case_service import (
    clear_cases,
    create_screening_case,
    get_all_cases,
    get_case_by_id,
    recapture_case,
    submit_specialist_review,
)
from backend.app.schemas.cases import SpecialistReviewRequest

client = TestClient(app)


def _make_dummy_report(grade=0, is_gradable=True, sample_id="sample_test"):
    """Helper to synthesize structured screening report dictionary for unit testing workflow routing."""
    grade_labels = {
        0: "No DR",
        1: "Mild DR",
        2: "Moderate DR",
        3: "Severe DR",
        4: "Proliferative DR",
    }
    recommendations = {
        0: "No Diabetic Retinopathy detected. Routine annual eye screening recommended.",
        1: "Mild Diabetic Retinopathy detected. Schedule follow-up screening in 6-12 months.",
        2: "Moderate Diabetic Retinopathy detected. Referral to Ophthalmologist for evaluation within 4-6 weeks.",
        3: "Severe Diabetic Retinopathy detected. Urgent referral to Retina Specialist within 1-2 weeks.",
        4: "Proliferative Diabetic Retinopathy detected. IMMEDIATE referral to Retina Specialist for urgent treatment.",
    }

    if not is_gradable:
        return {
            "sample_id": sample_id,
            "original_image_path": None,
            "image_quality": {
                "score": 0.2,
                "status": "ungradable",
                "issues": ["Low resolution", "Severe blur"],
                "metrics": {"blur": 15.0},
            },
            "dr_prediction": None,
            "explanation": None,
            "recommendation": "Image quality insufficient. Please recapture.",
            "disclaimer": "AI-assisted screening tool.",
        }

    return {
        "sample_id": sample_id,
        "original_image_path": f"/outputs/explainability/original_{sample_id}.png",
        "image_quality": {
            "score": 0.88,
            "status": "gradable",
            "issues": [],
            "metrics": {"blur": 150.0},
        },
        "dr_prediction": {
            "grade": grade,
            "label": grade_labels[grade],
            "confidence": 0.94,
            "probabilities": {grade_labels[i]: (0.94 if i == grade else 0.015) for i in range(5)},
            "uncertainty": {
                "entropy": 0.12,
                "margin": 0.92,
            },
        },
        "explanation": {
            "gradcam_path": f"/outputs/explainability/gradcam_{sample_id}.png",
            "original_image_path": f"/outputs/explainability/original_{sample_id}.png",
            "target_class": grade,
        },
        "recommendation": recommendations[grade],
        "disclaimer": "AI-assisted screening tool.",
    }


def setup_function():
    """Reset case database before each test."""
    clear_cases()


def test_1_grade_0_no_dr_routine_no_specialist_queue():
    """Test 1: Grade 0 (No DR) generates ROUTINE_SCREENING and is NOT enqueued into specialist queue."""
    report = _make_dummy_report(grade=0, is_gradable=True, sample_id="grade0_sample")
    case = create_screening_case(report)

    # 1. Exact status must be ROUTINE_SCREENING
    assert case.status == "ROUTINE_SCREENING"
    assert case.case_id == "case_grade0_sample"

    # 2. Case must NOT appear in specialist queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert not any(c.case_id == case.case_id for c in specialist_queue)

    # 3. Direct specialist review on routine screening is rejected
    with pytest.raises(Exception) as exc_info:
        submit_specialist_review(
            case.case_id,
            SpecialistReviewRequest(decision="CONFIRMED", specialist_notes="Testing rejection"),
        )
    assert "does not require specialist review" in str(exc_info.value)


def test_2_grade_1_mild_dr_followup_no_specialist_queue():
    """Test 2: Grade 1 (Mild DR) generates FOLLOW_UP_RECOMMENDED and is NOT enqueued into specialist queue."""
    report = _make_dummy_report(grade=1, is_gradable=True, sample_id="grade1_sample")
    case = create_screening_case(report)

    # 1. Exact status must be FOLLOW_UP_RECOMMENDED
    assert case.status == "FOLLOW_UP_RECOMMENDED"
    assert case.case_id == "case_grade1_sample"

    # 2. Case must NOT appear in specialist queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert not any(c.case_id == case.case_id for c in specialist_queue)


def test_3_grade_2_moderate_dr_specialist_review():
    """Test 3: Grade 2 (Moderate DR) generates REQUIRES_SPECIALIST_REVIEW and is enqueued into specialist queue."""
    report = _make_dummy_report(grade=2, is_gradable=True, sample_id="grade2_sample")
    case = create_screening_case(report)

    # 1. Exact status must be REQUIRES_SPECIALIST_REVIEW
    assert case.status == "REQUIRES_SPECIALIST_REVIEW"

    # 2. Case MUST appear in specialist queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert any(c.case_id == case.case_id for c in specialist_queue)


def test_4_grade_3_severe_dr_specialist_review():
    """Test 4: Grade 3 (Severe DR) generates REQUIRES_SPECIALIST_REVIEW and is enqueued into specialist queue."""
    report = _make_dummy_report(grade=3, is_gradable=True, sample_id="grade3_sample")
    case = create_screening_case(report)

    # 1. Exact status must be REQUIRES_SPECIALIST_REVIEW
    assert case.status == "REQUIRES_SPECIALIST_REVIEW"

    # 2. Case MUST appear in specialist queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert any(c.case_id == case.case_id for c in specialist_queue)


def test_5_grade_4_proliferative_dr_urgent_specialist_review():
    """Test 5: Grade 4 (Proliferative DR) generates URGENT_SPECIALIST_REVIEW and is enqueued into specialist queue."""
    report = _make_dummy_report(grade=4, is_gradable=True, sample_id="grade4_sample")
    case = create_screening_case(report)

    # 1. Exact status must be URGENT_SPECIALIST_REVIEW
    assert case.status == "URGENT_SPECIALIST_REVIEW"

    # 2. Case MUST appear in specialist queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert any(c.case_id == case.case_id for c in specialist_queue)


def test_6_ungradable_recapture_required_no_direct_specialist_review():
    """Test 6: Ungradable image generates RECAPTURE_REQUIRED and is not directly sent to specialist review."""
    report = _make_dummy_report(is_gradable=False, sample_id="ungradable_sample")
    case = create_screening_case(report)

    # 1. Exact status must be RECAPTURE_REQUIRED
    assert case.status == "RECAPTURE_REQUIRED"

    # 2. Initial ungradable case must not be in specialist review queue
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert not any(c.case_id == case.case_id for c in specialist_queue)

    # 3. Submitting specialist review on ungradable case is blocked
    with pytest.raises(Exception) as exc_info:
        submit_specialist_review(
            case.case_id,
            SpecialistReviewRequest(decision="CONFIRMED", specialist_notes="Invalid review"),
        )
    assert "Case has already been decided." in str(exc_info.value) or "does not require specialist review" in str(exc_info.value)


def test_7_specialist_confirm_complete():
    """Test 7: Specialist Confirm transitions status to CONFIRMED (review complete, locks case)."""
    report = _make_dummy_report(grade=2, sample_id="confirm_workflow_sample")
    case = create_screening_case(report)
    assert case.status == "REQUIRES_SPECIALIST_REVIEW"

    updated = submit_specialist_review(
        case.case_id,
        SpecialistReviewRequest(
            decision="CONFIRMED",
            specialist_notes="Verified retinal microaneurysms and exudates.",
            specialist_id="dr_retina_specialist",
        ),
    )
    # Review COMPLETE: Status transitions to CONFIRMED
    assert updated.status == "CONFIRMED"
    assert updated.specialist_decision == "CONFIRMED"

    # Second decision attempt must be rejected (locked state)
    with pytest.raises(Exception):
        submit_specialist_review(
            case.case_id,
            SpecialistReviewRequest(decision="OVERRIDDEN", override_grade=3),
        )


def test_8_specialist_override_complete():
    """Test 8: Specialist Override transitions status to OVERRIDDEN with override_grade (review complete, locks case)."""
    report = _make_dummy_report(grade=2, sample_id="override_workflow_sample")
    case = create_screening_case(report)
    assert case.status == "REQUIRES_SPECIALIST_REVIEW"

    updated = submit_specialist_review(
        case.case_id,
        SpecialistReviewRequest(
            decision="OVERRIDDEN",
            override_grade=4,
            specialist_notes="Neovascularization at disc observed. Escalating to Proliferative DR.",
            specialist_id="dr_retina_specialist",
        ),
    )
    # Review COMPLETE: Status transitions to OVERRIDDEN with new grade
    assert updated.status == "OVERRIDDEN"
    assert updated.override_grade == 4
    assert updated.specialist_decision == "OVERRIDDEN"

    # Second decision attempt must be rejected
    with pytest.raises(Exception):
        submit_specialist_review(
            case.case_id,
            SpecialistReviewRequest(decision="CONFIRMED"),
        )


def test_9_specialist_recapture_new_image_required():
    """Test 9: Specialist Request Recapture transitions to RECAPTURE_REQUIRED and requires fresh image."""
    report = _make_dummy_report(grade=3, sample_id="recapture_workflow_sample")
    case = create_screening_case(report)
    assert case.status == "REQUIRES_SPECIALIST_REVIEW"

    # Step A: Specialist requests recapture
    updated = submit_specialist_review(
        case.case_id,
        SpecialistReviewRequest(
            decision="REQUEST_RECAPTURE",
            specialist_notes="Dust artifact on sensor obscures macula. Please recapture.",
            specialist_id="dr_retina_specialist",
        ),
    )
    assert updated.status == "RECAPTURE_REQUIRED"
    assert updated.specialist_decision == "REQUEST_RECAPTURE"

    # Case requested for recapture by specialist IS tracked
    specialist_queue = get_all_cases(specialist_queue_only=True)
    assert any(c.case_id == case.case_id for c in specialist_queue)

    # Step B: New image uploaded (Recapture attempt 2 with clear Grade 2 image)
    new_report = _make_dummy_report(grade=2, sample_id="recapture_attempt2")
    recaptured_case = recapture_case(case.case_id, new_report)

    assert recaptured_case.attempt == 2
    assert recaptured_case.status == "REQUIRES_SPECIALIST_REVIEW"
    assert recaptured_case.specialist_decision is None
    assert len(recaptured_case.history) == 2
    assert recaptured_case.history[0].specialist_decision == "REQUEST_RECAPTURE"

    # Step C: Specialist can now confirm attempt 2
    final_case = submit_specialist_review(
        case.case_id,
        SpecialistReviewRequest(
            decision="CONFIRMED",
            specialist_notes="Replacement scan is clear. Diagnosis confirmed.",
            specialist_id="dr_retina_specialist",
        ),
    )
    assert final_case.status == "CONFIRMED"
