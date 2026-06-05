import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allows the Android device on the network to connect to the dev server
  allowedDevOrigins: ['192.168.137.83', '192.168.137.1', 'localhost', '*', '192.168.137.198'],
  // Required for Capacitor to build static HTML/JS/CSS bundle into the 'out' directory
  output: 'export',
  // Disable image optimization because static export doesn't support the Next.js image server natively
  images: { unoptimized: true }
};

export default nextConfig;
