import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_INTERNAL_API_URL || 'http://pixelforge-backend:8206/api/:path*',
      },
    ];
  },
};

export default nextConfig;
