import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Netra - Explainable AI for Diabetic Retinopathy Screening',
  description: 'Explainable AI solution for Diabetic Retinopathy Screening in Rural India (Smart India Hackathon 2026)',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="light">
      <body>{children}</body>
    </html>
  );
}
