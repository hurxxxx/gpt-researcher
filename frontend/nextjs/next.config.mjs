/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
    domains: ['www.google.com', 'www.google-analytics.com'],
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
  output: 'standalone',
  distDir: '.next',
  experimental: {
    appDir: true,
  },
};

export default nextConfig;
