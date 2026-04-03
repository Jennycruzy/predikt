/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 50: "#F0ECE2", 100: "#E0D9C8", 200: "#C4BAA3", 900: "#0E0D0A", 800: "#1A1814", 700: "#252320" },
        mint: { 400: "#00D4AA", 500: "#00B894" },
        flame: { 400: "#FF6B35", 500: "#FF3366" },
        amber: { 400: "#FFB800" },
        violet: { 400: "#A855F7" },
        cyan: { 400: "#4ECDC4" },
      },
      fontFamily: {
        mono: ["'DM Mono'", "monospace"],
        sans: ["'DM Sans'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
