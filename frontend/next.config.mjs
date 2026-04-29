/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // plotly.js-dist-min is browser-only; keep it out of server bundles.
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.externals = [...(config.externals || []), 'plotly.js-dist-min'];
    }
    return config;
  },
};

export default nextConfig;
