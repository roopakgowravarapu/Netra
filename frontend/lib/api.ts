/**
 * API client for communicating with Netra FastAPI Backend.
 */

export interface QualityMetrics {
  width?: number;
  height?: number;
  laplacian_var?: number;
  brightness_mean?: number;
  contrast_std?: number;
  fov_ratio?: number;
}

export interface ImageQuality {
  score: number;
  status: "gradable" | "ungradable";
  issues: string[];
  rejection_reason?: string;
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
  probabilities: Record<string, number>;
  uncertainty: UncertaintyMetrics;
}

export interface Explanation {
  gradcam_path?: string;
  original_image_path?: string;
  target_class: number;
}

export interface ScreeningReport {
  sample_id: string;
  case_id?: string;
  original_image_path?: string;
  image_quality: ImageQuality;
  dr_prediction?: DRPrediction | null;
  explanation?: Explanation | null;
  recommendation: string;
  disclaimer: string;
}

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

export async function uploadAndAnalyzeImage(file: File): Promise<ScreeningReport> {
  const formData = new FormData();
  formData.append("file", file);

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

export function getStaticImageUrl(relativePath: string | undefined): string | null {
  if (!relativePath) return null;
  // If path starts with http/https, return as is
  if (relativePath.startsWith("http://") || relativePath.startsWith("https://")) {
    return relativePath;
  }
  // Convert local filesystem relative path to backend /static endpoint URL
  const normalized = relativePath.replace(/\\/g, "/");
  const filename = normalized.split("/").pop();
  return `${API_BASE_URL}/static/explainability/${filename}`;
}
