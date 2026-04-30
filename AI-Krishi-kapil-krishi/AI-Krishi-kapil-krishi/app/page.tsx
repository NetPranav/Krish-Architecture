import Link from "next/link";
import LeafLogo from "@/app/components/ui/LeafLogo";

export default function Home() {
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
          <a href="/register" className="btn btn-primary" id="btn-get-started">
            Get Started
          </a>
          <a href="/login" className="btn btn-outline" id="btn-login">
            Login
          </a>
        </div>
      </div>
    </main>
  );
}
