'use client';

interface SelectOption {
  value: string;
  label: string;
}

interface FormSelectProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  leadingIcon?: React.ReactNode;
}

export default function FormSelect({
  id,
  label,
  value,
  onChange,
  options,
  placeholder,
  error,
  leadingIcon,
}: FormSelectProps) {
  return (
    <div className="form-field">
      <label htmlFor={id} className="form-label">
        {label}
      </label>
      <div className={`form-input-wrapper ${error ? 'form-input-error' : ''}`}>
        {leadingIcon && <span className="form-input-icon">{leadingIcon}</span>}
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`form-select ${!value ? 'form-select-placeholder' : ''}`}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <span className="form-select-chevron">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </div>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
