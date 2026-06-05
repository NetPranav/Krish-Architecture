'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import LeafLogo from '@/app/components/ui/LeafLogo';
import FormInput from '@/app/components/ui/FormInput';
import FormSelect from '@/app/components/ui/FormSelect';

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी' },
  { value: 'mr', label: 'मराठी' },
  { value: 'gu', label: 'ગુજરાતી' },
  { value: 'pa', label: 'ਪੰਜਾਬੀ' },
  { value: 'bn', label: 'বাংলা' },
  { value: 'ta', label: 'தமிழ்' },
  { value: 'te', label: 'తెలుగు' },
  { value: 'kn', label: 'ಕನ್ನಡ' },
];

const operationOptions = [
  { value: 'crop', label: 'Crop Farming' },
  { value: 'dairy', label: 'Dairy Farming' },
  { value: 'poultry', label: 'Poultry Farming' },
  { value: 'horticulture', label: 'Horticulture' },
  { value: 'fishery', label: 'Fishery' },
  { value: 'organic', label: 'Organic Farming' },
  { value: 'mixed', label: 'Mixed Farming' },
  { value: 'other', label: 'Other' },
];

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState('en');
  const [operation, setOperation] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!fullName.trim()) newErrors.fullName = 'Full name is required.';
    if (!phone.trim()) {
      newErrors.phone = 'Phone number is required.';
    } else if (!/^\d{10}$/.test(phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Enter a valid 10-digit mobile number.';
    }
    if (!password) {
      newErrors.password = 'Password is required.';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters.';
    }
    if (!operation) newErrors.operation = 'Please select your primary operation.';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleContinue = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validate()) return;

    setLoading(true);
    try {
      const { register } = await import('@/app/lib/api');
      const res = await register(fullName, phone, password, language, operation);
      if (res?.status === 'success') {
        if (res.token) localStorage.setItem('smartagri_token', res.token);
        router.push('/dashboard');
      } else {
        setErrors({ form: res?.message || 'Registration failed.' });
      }
    } catch (err: any) {
      setErrors({ form: err.message || 'Error connecting to server.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-card">
      {/* Header */}
      <div className="auth-header">
        <LeafLogo size={44} variant="seedling" />
        <h1 className="auth-title auth-title--green">Create Account</h1>
        <p className="auth-subtitle">Step 1 of 3: Personal Details</p>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: '33%' }} />
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleContinue} noValidate>
        {errors.form && <p className="form-error" style={{ marginBottom: 16, textAlign: 'center' }}>{errors.form}</p>}
        
        <FormInput
          id="register-name"
          label="Full Name"
          type="text"
          placeholder="Enter your full name"
          value={fullName}
          onChange={(val) => {
            setFullName(val);
            if (errors.fullName) setErrors((e) => ({ ...e, fullName: '' }));
          }}
          error={errors.fullName}
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          }
        />

        <FormInput
          id="register-phone"
          label="Phone Number"
          type="tel"
          placeholder="10-digit mobile number"
          value={phone}
          onChange={(val) => {
            const cleaned = val.replace(/\D/g, '').slice(0, 10);
            setPhone(cleaned);
            if (errors.phone) setErrors((e) => ({ ...e, phone: '' }));
          }}
          error={errors.phone}
          prefix="+91"
        />

        <FormInput
          id="register-password"
          label="Password"
          type="password"
          placeholder="Create a password"
          value={password}
          onChange={(val) => {
            setPassword(val);
            if (errors.password) setErrors((e) => ({ ...e, password: '' }));
          }}
          error={errors.password}
          showPasswordToggle
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          }
        />

        <FormSelect
          id="register-language"
          label="Preferred Language"
          value={language}
          onChange={setLanguage}
          options={languageOptions}
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 8l6 6" />
              <path d="M4 14l6-6 2-3" />
              <path d="M2 5h12" />
              <path d="M7 2h1" />
              <path d="M22 22l-5-10-5 10" />
              <path d="M14 18h6" />
            </svg>
          }
        />

        <FormSelect
          id="register-operation"
          label="Primary Operation"
          value={operation}
          onChange={(val) => {
            setOperation(val);
            if (errors.operation) setErrors((e) => ({ ...e, operation: '' }));
          }}
          options={operationOptions}
          placeholder="Select operation type"
          error={errors.operation}
          leadingIcon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22c1-5 7-7.5 7-12a7 7 0 1 0-14 0c0 4.5 6 7 7 12z" />
              <circle cx="12" cy="10" r="2" />
            </svg>
          }
        />

        <button
          type="submit"
          className="btn btn-primary"
          id="btn-register-continue"
          disabled={loading}
          style={{ opacity: loading ? 0.7 : 1, marginTop: 8 }}
        >
          {loading ? 'Processing...' : 'Create Account'}
        </button>
      </form>

      {/* Footer */}
      <p className="auth-footer-signup">
        Already have an account?{' '}
        <Link href="/login">Sign In</Link>
      </p>
    </div>
  );
}
