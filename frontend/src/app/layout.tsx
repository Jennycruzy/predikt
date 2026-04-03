import "./globals.css";

export const metadata = {
  title: "PREDIKT — Reasoning-Driven Prediction Markets",
  description: "AI validators debate, challenge reasoning, and converge on predictions through intelligence-weighted predikt on GenLayer Studionet.",
};

import Providers from "../components/Providers";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
