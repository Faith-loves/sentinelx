import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: ".next-build",
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
