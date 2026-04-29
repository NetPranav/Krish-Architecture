'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import LeafLogo from '@/app/components/ui/LeafLogo';
import FormInput from '@/app/components/ui/FormInput';

export default function LoginPage() {
  const router = useRouter();
  const [emailOrPhone, setEmailOrPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (!emailOrPhone.trim()) {
      setError('Please enter your phone number or email.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      router.push('/dashboard');
    }, 800);
  };

  const handleOtpLogin = () => {
    // TODO: Navigate to OTP screen
    alert('OTP login flow coming soon!');
  };

  return (
    <div className="auth-card">
      {/* Header */}
      <div className="auth-header">
        <LeafLogo size={44} variant="leaf" />
        <h1 className="auth-title">Welcome Back</h1>
        <p className="auth-subtitle">Sign in to access your farm dashboard.</p>
      </div>

      {/* Form */}
      <form onSubmit={handleLogin} noValidate>
        <FormInput
          id="login-email"
          label="Phone Number / Email"
          type="text"
          placeholder="Enter details"
          value={emailOrPhone}
          onChange={setEmailOrPhone}
          hint="Enter mobile number / मोबाइल नंबर दर्ज करें"
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          }
        />

        <FormInput
          id="login-password"
          label="Password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={setPassword}
          showPasswordToggle
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          }
        />

        <Link href="#" className="forgot-link">
          Forgot Password?
        </Link>

        {error && <p className="form-error" style={{ marginBottom: 16, textAlign: 'center' }}>{error}</p>}

        <button
          type="submit"
          className="btn btn-primary"
          id="btn-login-submit"
          disabled={loading}
          style={{ opacity: loading ? 0.7 : 1 }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      {/* OR divider */}
      <div className="auth-divider">
        <div className="auth-divider-line" />
        <span className="auth-divider-text">OR</span>
        <div className="auth-divider-line" />
      </div>

      {/* OTP Button */}
      <button
        type="button"
        className="btn btn-secondary"
        id="btn-otp-login"
        onClick={handleOtpLogin}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2" />
          <path d="M7 15h0M12 15h0M17 15h0M7 10h0M12 10h0M17 10h0" />
        </svg>
        Login with OTP
      </button>

      {/* Register Link */}
      <p className="auth-footer-signup">
        Don&apos;t have an account?{' '}
        <Link href="/register">Register</Link>
      </p>

      {/* Footer */}
      <p className="auth-footer">
        By logging in, you agree to our{' '}
        <Link href="#">Terms of Service</Link>
        <br />
        and <Link href="#">Privacy Policy</Link>.
      </p>
    </div>
  );
}
