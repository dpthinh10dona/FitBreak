import React from 'react';

export const CoinIcon = ({ size = 16, className = "" }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ display: 'inline-block', verticalAlign: '-0.15em', flexShrink: 0 }}
  >
    <circle cx="12" cy="12" r="10" fill="url(#coinGradient)" stroke="#d97706" strokeWidth="1.5" />
    <circle cx="12" cy="12" r="7.5" stroke="#fef08a" strokeWidth="1" strokeDasharray="2 2" opacity="0.8" />
    <text
      x="12"
      y="16"
      textAnchor="middle"
      fontSize="11"
      fontWeight="900"
      fontFamily="sans-serif"
      fill="#78350f"
    >
      C
    </text>
    <defs>
      <linearGradient id="coinGradient" x1="4" y1="4" x2="20" y2="20" gradientUnits="userSpaceOnUse">
        <stop stopColor="#fef08a" />
        <stop offset="0.5" stopColor="#f59e0b" />
        <stop offset="1" stopColor="#b45309" />
      </linearGradient>
    </defs>
  </svg>
);

export default CoinIcon;
