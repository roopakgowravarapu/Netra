/**
 * API client for communicating with Netra FastAPI Backend.
 */

export * from "./types";
import type {
    QualityMetrics,
    ImageQuality,
    UncertaintyMetrics,
    DRPrediction,
    Explanation,
    RetinalStructures,
    LesionEvidence,
    SpatialZone,
    SpatialAnalysis,
    RetinalAnalysis,
    ScreeningReport,
    ScreeningVisit,
    PatientRecord,
    PatientProgressionComparison,
    CaseAuditEntry,
    CaseHistoryItem,
    CaseItem,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function checkBackendHealth(): Promise<boolean> {
    try {
        const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
        if (!res.ok) return false;
        const data = await res.json();
        return data.status === "ok";
    } catch (err) {
        return false;
    }
}

export interface PatientIntakePayload {
    patient_id?: string;
    patient_name?: string;
    age?: number;
    gender?: string;
    diabetes_type?: string;
    diabetes_duration_years?: number;
    eye_examined?: string;
    patient_consent?: boolean;
    case_id?: string;
}

export async function uploadAndAnalyzeImage(
    file: File,
    intake?: PatientIntakePayload | string,
    legacyCaseId?: string
): Promise<ScreeningReport> {
    const formData = new FormData();
    formData.append("file", file);

    if (typeof intake === "string") {
        formData.append("patient_name", intake);
        if (legacyCaseId) formData.append("case_id", legacyCaseId);
    } else if (intake) {
        if (intake.patient_id) formData.append("patient_id", intake.patient_id);
        if (intake.patient_name) formData.append("patient_name", intake.patient_name);
        if (intake.age !== undefined && intake.age !== null) formData.append("age", intake.age.toString());
        if (intake.gender) formData.append("gender", intake.gender);
        if (intake.diabetes_type) formData.append("diabetes_type", intake.diabetes_type);
        if (intake.diabetes_duration_years !== undefined && intake.diabetes_duration_years !== null) {
            formData.append("diabetes_duration_years", intake.diabetes_duration_years.toString());
        }
        if (intake.eye_examined) formData.append("eye_examined", intake.eye_examined);
        if (intake.patient_consent !== undefined) formData.append("patient_consent", String(intake.patient_consent));
        if (intake.case_id) formData.append("case_id", intake.case_id);
    }

    const res = await fetch(`${API_BASE_URL}/predict`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        let errorDetail = "API request failed";
        try {
            const errData = await res.json();
            errorDetail = errData.detail || errorDetail;
        } catch {
            // fallback text
        }
        throw new Error(errorDetail);
    }

    const report: ScreeningReport = await res.json();
    return report;
}

// Telemedicine API calls
export async function fetchTelemedicineCases(all: boolean = false): Promise<CaseItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/cases?all=${all}`, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch telemedicine queue");
    return await res.json();
}

export async function submitSpecialistReview(
    caseId: string,
    decision: "CONFIRMED" | "OVERRIDDEN" | "REQUEST_RECAPTURE" | string,
    overrideGrade?: number,
    notes?: string,
    specialistId: string = "dr_ophthalmologist_01"
): Promise<CaseItem> {
    const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            decision,
            override_grade: overrideGrade,
            specialist_notes: notes || "",
            specialist_id: specialistId,
        }),
    });

    if (!res.ok) {
        let err = "Failed to submit review";
        try {
            const d = await res.json();
            err = d.detail || err;
        } catch { }
        throw new Error(err);
    }
    return await res.json();
}

export async function referCaseToDoctor(caseId: string, notes?: string): Promise<CaseItem> {
    const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/refer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ referral_notes: notes || "" }),
    });
    if (!res.ok) throw new Error("Failed to refer case to specialist");
    return await res.json();
}

export async function deleteCase(caseId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/cases/${encodeURIComponent(caseId)}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Failed to delete case ${caseId}`);
}

export async function deleteAllCases(): Promise<{ message: string; count: number }> {
    const res = await fetch(`${API_BASE_URL}/api/cases`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete all cases");
    return await res.json();
}

// Patient Management API calls
export async function fetchPatients(query?: string): Promise<PatientRecord[]> {
    const url = query ? `${API_BASE_URL}/api/patients?query=${encodeURIComponent(query)}` : `${API_BASE_URL}/api/patients`;
    const res = await fetch(url, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch patient records");
    return await res.json();
}

export async function deletePatient(patientId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Failed to delete patient ${patientId}`);
}

export async function clearPatientHistory(patientId: string): Promise<PatientRecord> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}/history`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error(`Failed to clear history for patient ${patientId}`);
    const data = await res.json();
    return data.patient;
}

export async function deleteAllPatients(): Promise<{ message: string; count: number }> {
    const res = await fetch(`${API_BASE_URL}/api/patients`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete all patient records");
    return await res.json();
}

export async function fetchPatientById(patientId: string): Promise<PatientRecord> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}`, { method: "GET" });
    if (!res.ok) throw new Error(`Patient ${patientId} not found`);
    return await res.json();
}

export async function fetchPatientProgression(patientId: string, eye?: string): Promise<PatientProgressionComparison> {
    const url = eye
        ? `${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}/progression?eye=${encodeURIComponent(eye)}`
        : `${API_BASE_URL}/api/patients/${encodeURIComponent(patientId)}/progression`;
    const res = await fetch(url, { method: "GET" });
    if (!res.ok) throw new Error("Failed to fetch progression comparison");
    return await res.json();
}

export async function createOrUpdatePatient(data: {
    patient_id?: string;
    name: string;
    age?: number;
    gender?: string;
    diabetes_type?: string;
    diabetes_duration_years?: number;
}): Promise<PatientRecord> {
    const res = await fetch(`${API_BASE_URL}/api/patients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to save patient demographic profile");
    return await res.json();
}

export function getStaticImageUrl(relativePath: string | null | undefined): string | null {
    if (!relativePath) return null;
    if (relativePath.startsWith("http://") || relativePath.startsWith("https://")) {
        return relativePath;
    }
    const normalized = relativePath.replace(/\\/g, "/");
    const filename = normalized.split("/").pop();
    return `${API_BASE_URL}/static/explainability/${filename}`;
}
