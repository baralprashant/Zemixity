import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Use environment variable for API URL in production, fallback to localhost in development
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: '**',
      }
    ],
  },
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // Set workspace root to silence Next.js warning about multiple lockfiles
  outputFileTracingRoot: __dirname,
};

// Validate environment in production
if (process.env.NODE_ENV === 'production') {
  console.log('🔍 Production build - validating configuration...');

  if (process.env.NEXT_PUBLIC_API_URL) {
    console.log(` API URL configured: ${process.env.NEXT_PUBLIC_API_URL}`);
  } else {
    console.warn('⚠️  NEXT_PUBLIC_API_URL not set - using default localhost (this may not work in production)');
  }
}

export default nextConfig;
