/**
 * Clinical Screening & AI Prediction Type Definitions.
 */

export interface QualityMetrics {
  width?: number;
  height?: number;
  laplacian_var?: number;
  raw_laplacian_var?: number;
  brightness_mean?: number;
  contrast_std?: number;
  green_mean?: number;
  fov_ratio?: number;
}

export interface ImageQuality {
  score: number;
  status: "gradable" | "borderline" | "ungradable" | string;
  issues: string[];
  rejection_reason?: string;
  retake_instructions?: string;
  enhancement_recommended?: boolean;
  metrics?: QualityMetrics;
}

export interface UncertaintyMetrics {
  entropy: number;
  margin: number;
}

export interface DRPrediction {
  grade: number;
  label: string;
  confidence: number;
  raw_confidence?: number;
  temperature?: number;
  probabilities: Record<string, number>;
  uncertainty: UncertaintyMetrics;
  uncertain_prediction?: boolean;
  uncertainty_warning?: string | null;
  macula_risk_level?: string;
  macula_risk_description?: string;
}

export interface Explanation {
  gradcam_path?: string;
  original_image_path?: string;
  heatmap_image_path?: string;
  highlighted_region?: string;
  xai_explanation?: {
    highlighted_region?: string;
    what_heatmap_shows?: string;
    why_this_matters?: string;
    model_interpretation?: string;
    disclaimer?: string;
  } | null;
  target_class: number;
  saliency_description?: string;
}

export interface RetinalStructures {
  optic_disc?: {
    x: number;
    y: number;
    radius: number;
    detected: boolean;
  } | null;
  fovea?: {
    x: number;
    y: number;
    detected: boolean;
  } | null;
  vessel_mask?: string | null;
  vessel_density: number;
}

export interface LesionEvidence {
  microaneurysms?: {
    detected: boolean;
    count: number;
  } | null;
  exudates?: {
    detected: boolean;
    count: number;
    area_pixels: number;
  } | null;
  hemorrhages?: {
    detected: boolean;
    count: number;
    dot_blot_count?: number;
    flame_count?: number;
    severity: string;
  } | null;
  neovascularization?: {
    detected: boolean;
    site?: string;
  } | null;
  lesion_overlay?: string | null;
}

export interface SpatialZone {
  zone_id: string;
  zone_name: string;
  short_code: string;
  status: "CLEAR" | "EARLY_SIGNS" | "ACTIVE_LESIONS" | "MACULAR_THREAT" | "CRITICAL_NEOVASCULARIZATION" | "ELEVATED_ATTENTION" | string;
  status_label: string;
  lesion_summary: string;
  microaneurysms_count: number;
  exudates_count: number;
  exudates_area_px: number;
  hemorrhages_count: number;
  neovascularization: boolean;
  attention_mean: number;
  attention_peak: number;
  anatomical_role: string;
  clinical_explanation: string;
}

export interface SpatialAnalysis {
  spatial_map_image?: string | null;
  macula_threat_level: "LOW_RISK" | "BORDERLINE" | "HIGH_THREAT" | string;
  quadrants_affected_count: number;
  affected_quadrants: string[];
  primary_attention_hotspot: string;
  zones: SpatialZone[];
}

export interface RetinalAnalysis {
  quality_status: "GOOD" | "BORDERLINE" | "UNGRADABLE" | string;
  quality_score: number;
  focus_score?: number;
  mean_illumination?: number;
  quality_feedback: string[];
  recapture_instructions?: string | null;
  enhancement_applied: boolean;
  enhanced_image?: string | null;
  retinal_structures?: RetinalStructures | null;
  lesion_evidence?: LesionEvidence | null;
  spatial_analysis?: SpatialAnalysis | null;
  dr_grade?: number | null;
  severity: string;
  referable_dr: boolean;
  raw_confidence: number;
  calibrated_confidence: number;
  calibration_status: string;
  gradcam_image?: string | null;
  gradcam_description: string;
  heatmap_image?: string | null;
  xai_explanation?: {
    highlighted_region?: string;
    what_heatmap_shows?: string;
    why_this_matters?: string;
    model_interpretation?: string;
    disclaimer?: string;
  } | null;
  lesion_evidence_image?: string | null;
  lesion_evidence_description: string;
  annotated_report?: string | null;
  referral_recommendation: string;
  triage_action?: string;
  clinical_rule_match?: string;
}

export interface ScreeningReport {
  sample_id: string;
  case_id?: string;
  patient_id?: string;
  patient_name?: string;
  age?: number;
  gender?: string;
  diabetes_type?: string;
  diabetes_duration_years?: number;
  eye_examined?: string;
  patient_consent?: boolean;
  screening_date?: string;
  screening_time?: string;
  created_at?: string;
  original_image_path?: string;
  image_quality: ImageQuality;
  dr_prediction?: DRPrediction | null;
  explanation?: Explanation | null;
  recommendation: string;
  disclaimer: string;
  retinal_analysis?: RetinalAnalysis | null;
}
