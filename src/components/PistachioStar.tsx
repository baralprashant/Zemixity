interface PistachioStarProps {
  size?: number;
  className?: string;
}

export function PistachioStar({ size = 32, className = '' }: PistachioStarProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
        fill="#93C572"
        stroke="#7AB055"
        strokeWidth="1"
        strokeLinejoin="round"
      />
    </svg>
  );
}
