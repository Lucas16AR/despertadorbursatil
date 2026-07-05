import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Panel · Despertador Bursátil",
  description: "Administración del reporte diario",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
