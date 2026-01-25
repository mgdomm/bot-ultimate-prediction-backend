import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bot Ultimate Prediction",
  description: "Predicciones deportivas",
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className="min-h-screen bg-[#0F172A] text-[#E5E7EB]"
      >
        {children}
      </body>
    </html>
  );
}
