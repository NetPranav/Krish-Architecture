'use client';

interface LeafLogoProps {
  size?: number;
  variant?: 'leaf' | 'seedling';
}

export default function LeafLogo({ size = 64, variant = 'leaf' }: LeafLogoProps) {
  const circleSize = size * 1.5;

  return (
    <div
      className="leaf-logo"
      style={{
        width: circleSize,
        height: circleSize,
        borderRadius: '50%',
        background: 'rgba(46, 125, 50, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {variant === 'leaf' ? (
        <svg
          width={size}
          height={size}
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Leaf shape */}
          <path
            d="M32 8C32 8 12 20 12 38C12 49 21 56 32 56C43 56 52 49 52 38C52 20 32 8 32 8Z"
            fill="none"
            stroke="#2E7D32"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Center vein */}
          <path
            d="M32 18V48"
            stroke="#2E7D32"
            strokeWidth="2"
            strokeLinecap="round"
          />
          {/* Side veins */}
          <path
            d="M32 26L22 34"
            stroke="#2E7D32"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M32 26L42 34"
            stroke="#2E7D32"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M32 34L24 40"
            stroke="#2E7D32"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M32 34L40 40"
            stroke="#2E7D32"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg
          width={size}
          height={size}
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Seedling stem */}
          <path
            d="M32 52V30"
            stroke="#2E7D32"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
          {/* Left leaf */}
          <path
            d="M32 36C32 36 20 32 18 22C18 22 28 18 32 30"
            fill="none"
            stroke="#2E7D32"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Right leaf */}
          <path
            d="M32 30C32 30 44 26 46 16C46 16 36 12 32 24"
            fill="none"
            stroke="#2E7D32"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Ground line */}
          <path
            d="M24 52H40"
            stroke="#2E7D32"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      )}
    </div>
  );
}
