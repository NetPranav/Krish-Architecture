import type { Metadata, Viewport } from "next";
import { Poppins, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  variable: "--font-noto-devanagari",
  subsets: ["devanagari"],
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AgriSmart AI — Your Personal Smart Farming Assistant",
  description:
    "AI-driven smart farming assistant for crop insights, weather alerts, and market intelligence. आपका अपना स्मार्ट खेती सहायक।",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${poppins.variable} ${notoDevanagari.variable}`}
      suppressHydrationWarning
    >
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
