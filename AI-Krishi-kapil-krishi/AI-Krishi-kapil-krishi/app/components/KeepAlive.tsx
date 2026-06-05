"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { App } from "@capacitor/app";

export default function KeepAlive() {
  const router = useRouter();

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

    // Capacitor Hardware Back Button handler
    const backListener = App.addListener('backButton', ({ canGoBack }) => {
      // If on the root page, auth pages, or main dashboard, exit the app natively
      const path = window.location.pathname;
      if (path === '/' || path === '/dashboard' || path === '/login') {
        App.exitApp();
      } else {
        // Otherwise, navigate back in Next.js history
        router.back();
      }
    });

    return () => {
      clearInterval(interval);
      backListener.then(listener => listener.remove());
    };
  }, [router]);

  return null; // This component doesn't render anything
}
