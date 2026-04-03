/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Force Next.js to transpile these ESM packages that have nested valtio deps
  transpilePackages: [
    "@wagmi/connectors",
    "@reown/appkit",
    "@reown/appkit-controllers",
    "@walletconnect/ethereum-provider",
    "derive-valtio",
  ],
  // Proxy /api/* → VPS backend so Vercel (HTTPS) can call the VPS (HTTP)
  // without mixed-content browser errors. Vercel's edge makes the request
  // server-side, so no CORS or protocol mismatch.
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_URL || "http://130.61.38.218:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
  webpack: (config) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
      "@react-native-async-storage/async-storage": false,
    };
    config.externals.push("pino-pretty", "lokijs", "encoding");
    return config;
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
