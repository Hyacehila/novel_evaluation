import type { NextConfig } from "next";


const apiHost = process.env.NOVEL_EVAL_API_HOST ?? "127.0.0.1";
const apiPort = process.env.NOVEL_EVAL_API_PORT ?? "8000";
const apiOrigin = `http://${apiHost}:${apiPort}`;

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
