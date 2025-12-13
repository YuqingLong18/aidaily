import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Increase build timeout and memory limits for data-heavy pages
  experimental: {
    // Help with build-time data fetching
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
