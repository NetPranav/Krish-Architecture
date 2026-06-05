"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import LeafLogo from "@/app/components/ui/LeafLogo";

export default function Home() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem("smartagri_token");
    if (token) {
      router.replace("/dashboard");
    } else {
      setIsChecking(false);
    }
  }, [router]);

  if (isChecking) {
    return (
      <main className="landing-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LeafLogo size={80} variant="leaf" />
      </main>
    );
  }

  return (
    <main className="landing-page">
      <div className="landing-content">
        <div className="landing-logo">
          <LeafLogo size={52} variant="leaf" />
        </div>

        <h1 className="landing-title">AgriSmart AI</h1>

        <p className="landing-subtitle">
          Your Personal Smart
          <br />
          Farming Assistant
        </p>

        <p className="landing-hindi">आपका अपना स्मार्ट खेती सहायक</p>

        <div className="landing-buttons">
          <Link href="/register" className="btn btn-primary" id="btn-get-started">
            Get Started
          </Link>
          <Link href="/login" className="btn btn-outline" id="btn-login">
            Login
          </Link>
        </div>
      </div>
    </main>
  );
}
