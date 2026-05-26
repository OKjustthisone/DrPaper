import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DrPaper - Personal AI Research Assistant",
  description: "A personal AI knowledge base and visual note-taking tool for deep research",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 text-slate-800" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
