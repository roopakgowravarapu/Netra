"""
Runnable Entry Point for Netra Explainable AI DR Screening Platform.

Usage:
  python app.py          -> Runs automated self-test on a valid case & an ungradeable blur case.
  python app.py --server -> Starts FastAPI server on http://localhost:8000
"""

import sys
import asyncio
import cv2
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure workspace root is in path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app as fastapi_app


def create_synthetic_valid_fundus() -> np.ndarray:
    """Generates a synthetic valid fundus image satisfying FoV, focus, and illumination criteria."""
    h, w = 512, 512
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Create circular retinal aperture (FOV)
    center = (w // 2, h // 2)
    radius = int(min(h, w) * 0.42)
    cv2.circle(img, center, radius, (20, 80, 180), -1)  # BGR reddish fundus background
    
    # Add Optic Disc (Bright yellow/white circular region)
    od_center = (center[0] + radius // 2, center[1] - radius // 4)
    cv2.circle(img, od_center, int(radius * 0.2), (180, 240, 255), -1)
    
    # Add crisp retinal vessel tree (for high sharpness/Tenengrad score)
    for angle in range(0, 360, 30):
        rad = np.deg2rad(angle)
        x2 = int(od_center[0] + radius * 0.8 * np.cos(rad))
        y2 = int(od_center[1] + radius * 0.8 * np.sin(rad))
        cv2.line(img, od_center, (x2, y2), (10, 20, 80), 3)
        
    # Add simulated MAs & exudates for DR testing
    cv2.circle(img, (center[0] - 50, center[1] + 30), 4, (10, 10, 240), -1)  # Microaneurysm
    cv2.circle(img, (center[0] + 40, center[1] + 60), 6, (0, 240, 240), -1)  # Exudate
    
    return img


def create_synthetic_blurry_fundus() -> np.ndarray:
    """Generates an ungradeable severely blurred fundus image (Focus score < 8.5)."""
    valid_img = create_synthetic_valid_fundus()
    # Apply strong Gaussian blur to simulate cataract / severe optical defocus
    blurry = cv2.GaussianBlur(valid_img, (55, 55), 35.0)
    return blurry


def run_self_tests():
    """Executes automated verification for both a valid fundus case and an ungradeable blur case."""
    print("=" * 70)
    print("NETRA DR SCREENING PIPELINE - RUNNABLE SYSTEM VERIFICATION TEST")
    print("=" * 70)
    
    client = TestClient(fastapi_app)
    
    # 1. Health check verification
    resp_health = client.get("/health")
    print(f"\n[1/3] GET /health -> Status: {resp_health.status_code}, Response: {resp_health.json()}")
    assert resp_health.status_code == 200, "Health check failed!"
    
    # 2. Test Valid Fundus Case
    print("\n[2/3] Testing POST /api/v1/screen with Valid Fundus Image...")
    valid_bgr = create_synthetic_valid_fundus()
    _, valid_encoded = cv2.imencode(".png", valid_bgr)
    
    files_valid = {"image": ("valid_fundus.png", valid_encoded.tobytes(), "image/png")}
    data_valid = {"patient_id": "PATIENT_TEST_VALID_001"}
    
    res_valid = client.post("/api/v1/screen", files=files_valid, data=data_valid)
    print(f"Status Code: {res_valid.status_code}")
    assert res_valid.status_code == 200, f"Valid scan failed: {res_valid.text}"
    
    json_valid = res_valid.json()
    print("Valid Scan Response Payload:")
    print(f"  Patient ID: {json_valid['patient_id']}")
    print(f"  Quality Status: {json_valid['quality_assessment']['status']}")
    print(f"  Focus Score: {json_valid['quality_assessment']['focus_score']}")
    print(f"  Illumination: {json_valid['quality_assessment']['mean_illumination']}")
    if json_valid.get("clinical_results"):
        print(f"  ICDR Grade: Level {json_valid['clinical_results']['icdr_grade']} ({json_valid['clinical_results']['severity_label']})")
        print(f"  Referable Confidence: {json_valid['clinical_results']['referable_confidence']*100:.1f}%")
        print(f"  Biomarkers: MAs={json_valid['clinical_results']['biomarker_counts']['microaneurysms']}, Exudates={json_valid['clinical_results']['biomarker_counts']['hard_exudates_area_px']}px")
    print(f"  Triage Action: {json_valid['triage_action']}")
    
    # 3. Test Ungradeable Blurry Fundus Case
    print("\n[3/3] Testing POST /api/v1/screen with Ungradeable Blurry Image...")
    blurry_bgr = create_synthetic_blurry_fundus()
    _, blurry_encoded = cv2.imencode(".png", blurry_bgr)
    
    files_blurry = {"image": ("blurry_fundus.png", blurry_encoded.tobytes(), "image/png")}
    data_blurry = {"patient_id": "PATIENT_TEST_BLURRY_002"}
    
    res_blurry = client.post("/api/v1/screen", files=files_blurry, data=data_blurry)
    print(f"Status Code: {res_blurry.status_code}")
    assert res_blurry.status_code == 200, f"Blurry scan failed: {res_blurry.text}"
    
    json_blurry = res_blurry.json()
    print("Ungradeable Blur Response Payload:")
    print(f"  Patient ID: {json_blurry['patient_id']}")
    print(f"  Quality Status: {json_blurry['quality_assessment']['status']}")
    print(f"  Focus Score: {json_blurry['quality_assessment']['focus_score']}")
    print(f"  Recapture Required: {json_blurry['quality_assessment']['recapture_required']}")
    print(f"  Recapture Feedback: {json_blurry['quality_assessment']['recapture_feedback']}")
    print(f"  Clinical Results: {json_blurry['clinical_results']} (Blocked for patient safety)")
    print(f"  Triage Action: {json_blurry['triage_action']}")
    
    assert json_blurry['quality_assessment']['status'] == "UNGRADABLE", "Expected UNGRADABLE status for severe blur!"
    assert json_blurry['quality_assessment']['recapture_required'] is True, "Expected recapture_required = True!"
    
    print("\n" + "=" * 70)
    print("[SUCCESS] ALL SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import uvicorn
        uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        run_self_tests()
