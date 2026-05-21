import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        panel: "#101828",
        mist: "#eef2ff",
        sky: "#38bdf8",
        mint: "#34d399",
        amber: "#f59e0b",
        rose: "#fb7185",
        sand: "#f8f5ef"
      },
      boxShadow: {
        panel: "0 24px 80px rgba(15, 23, 42, 0.14)"
      }
    }
  },
  plugins: []
};

export default config;
