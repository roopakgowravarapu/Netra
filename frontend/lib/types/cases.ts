/**
 * Telemedicine Case & Review Queue Types.
 */

import { ScreeningReport } from "./screening";

export interface CaseAuditEntry {
  timestamp: string;
  actor: string;
  action: string;
  details?: string | null;
}

export interface CaseHistoryItem {
  attempt: number;
  timestamp: string;
  screening_report: ScreeningReport;
  specialist_decision?: string | null;
  override_grade?: number | null;
  specialist_notes?: string | null;
  specialist_id?: string | null;
}

export interface CaseItem {
  case_id: string;
  patient_id?: string | null;
  patient_name?: string;
  age?: number | null;
  gender?: string | null;
  diabetes_type?: string | null;
  diabetes_duration_years?: number | null;
  eye_examined?: string | null;
  patient_consent?: boolean;
  created_at: string;
  status: string;
  specialist_decision?: string | null;
  override_grade?: number | null;
  specialist_notes?: string | null;
  specialist_id?: string | null;
  updated_at?: string | null;
  attempt?: number;
  clinical_approval?: "APPROVED" | "REJECTED" | string | null;
  clinical_approved_at?: string | null;
  clinical_approved_by?: string | null;
  clinical_approval_notes?: string | null;
  referred_to_doctor?: boolean;
  referred_at?: string | null;
  referred_by?: string | null;
  referral_notes?: string | null;
  history?: CaseHistoryItem[];
  audit_trail?: CaseAuditEntry[];
  screening_report: ScreeningReport;
}
