import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allows the Android device on the network to connect to the dev server
  allowedDevOrigins: ['192.168.137.83', '192.168.137.1', 'localhost', '*', '192.168.137.198'],
};

export default nextConfig;
