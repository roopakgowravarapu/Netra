/**
 * Patient Record & Longitudinal Progression Types.
 */

export interface ScreeningVisit {
  visit_id: string;
  date: string;
  sample_id: string;
  case_id?: string | null;
  eye_examined: string;
  image_path?: string | null;
  iqa_status: string;
  dr_grade?: number | null;
  dr_stage?: string | null;
  confidence?: number | null;
  uncertain_prediction?: boolean;
  macula_risk_level?: string | null;
  specialist_status?: string | null;
  specialist_grade?: number | null;
  specialist_notes?: string | null;
}

export interface PatientRecord {
  patient_id: string;
  name: string;
  age?: number | null;
  gender?: string | null;
  diabetes_type?: string | null;
  diabetes_duration_years?: number | null;
  created_at: string;
  updated_at: string;
  visits: ScreeningVisit[];
}

export interface PatientProgressionComparison {
  patient_id: string;
  patient_name: string;
  eye_examined: string;
  baseline_visit?: ScreeningVisit | null;
  current_visit?: ScreeningVisit | null;
  grade_change?: number | null;
  progression_summary: string;
  disclaimer: string;
}
