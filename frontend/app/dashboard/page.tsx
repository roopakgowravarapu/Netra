import { redirect } from "next/navigation";

/**
 * Dashboard route redirected to unified Doctor Portal.
 * Eliminates duplicate portal while maintaining backwards-compatible routing.
 */
export default function DashboardRedirect() {
  redirect("/doctor");
}
