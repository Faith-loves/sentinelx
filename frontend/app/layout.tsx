import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelX | Autonomous Threat Hunting",
  description: "A polished SOC dashboard for autonomous threat detection, investigation, AI analysis, and reporting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
