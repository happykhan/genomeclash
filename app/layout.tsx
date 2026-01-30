import "./globals.css";
import Link from "next/link";
import { Space_Grotesk, IBM_Plex_Serif } from "next/font/google";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

const body = IBM_Plex_Serif({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

export const metadata = {
  title: "Genome Clash",
  description: "A genomics stat-comparison card game for bacterial genomes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>
        <div className="site">
          <header className="site-header">
            <div className="brand">
              <span className="brand-mark">GC</span>
              <div>
                <p className="brand-title">Genome Clash</p>
                <p className="brand-subtitle">Bacterial genome trading cards</p>
              </div>
            </div>
            <nav className="nav">
              <Link href="/">Cards</Link>
              <Link href="/about">About</Link>
              <Link href="/how-to-play">How to Play</Link>
              <Link href="/print-and-play">Print & Play</Link>
            </nav>
          </header>
          <main className="site-main">{children}</main>
          <footer className="site-footer">
            Educational project using NCBI reference genomes.
          </footer>
        </div>
      </body>
    </html>
  );
}
