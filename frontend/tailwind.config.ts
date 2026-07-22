import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 다크 럭셔리 BI 팔레트 (디자인 토큰)
        ink: {
          950: "#0a0e14",
          900: "#0f1520",
          850: "#141b28",
          800: "#1b2433",
          700: "#263141",
          600: "#374151",
        },
        line: "#243044",
        accent: {
          DEFAULT: "#5eead4", // teal
          soft: "#2dd4bf",
          deep: "#0d9488",
        },
        gold: "#e5b567",
        pos: "#34d399", // 상승
        neg: "#f87171", // 하락
        muted: "#8ba0bd",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 30px -12px rgba(0,0,0,0.6)",
        glow: "0 0 0 1px rgba(94,234,212,0.15), 0 10px 40px -12px rgba(94,234,212,0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
