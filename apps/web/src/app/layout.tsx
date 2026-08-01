import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GovCon Intelligence",
  description: "Contractor teaming intelligence for federal opportunities",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
