'use client';

import { motion } from 'framer-motion';

interface LogoProps {
  className?: string;
  size?: number;
  isLoading?: boolean;
}

export function Logo({ className = '', size = 60, isLoading = false }: LogoProps) {
  return (
    <motion.div
      className={`inline-flex items-center justify-center ${className}`}
      animate={isLoading ? { rotate: 360 } : {}}
      transition={
        isLoading
          ? {
              duration: 2,
              repeat: Infinity,
              ease: 'linear',
            }
          : {}
      }
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* 5-pointed star - pistachio color with stroke (same as sidebar) */}
        <path
          d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
          fill="#93C572"
          stroke="#7AB055"
          strokeWidth="1"
          strokeLinejoin="round"
        />
      </svg>
    </motion.div>
  );
}
