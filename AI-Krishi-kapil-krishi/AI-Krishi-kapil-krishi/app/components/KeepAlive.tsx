"use client";

import { useEffect } from "react";
import { getDashboard } from "@/app/lib/api";

export default function KeepAlive() {
  useEffect(() => {
    // Ping the backend immediately on load to ensure it's awake
    const pingBackend = async () => {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/`);
      } catch (error) {
        // Silently fail if there's a network issue
      }
    };

    pingBackend();

    // Render free tier spins down after 15 mins of inactivity.
    // Ping every 10 minutes (600,000 ms) to keep it alive while the app is open.
    const interval = setInterval(pingBackend, 10 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return null; // This component doesn't render anything
}
