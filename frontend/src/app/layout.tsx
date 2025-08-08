import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Daisler Print Analyzer",
  description: "Upload an image and get print-ready guidance",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="min-h-screen">
          <header className="sticky top-0 z-10 glass">
            <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="badge">Beta</div>
                <h1 className="text-lg font-semibold">Daisler Print Analyzer</h1>
              </div>
              <a
                href="https://nextjs.org"
                target="_blank"
                rel="noreferrer"
                className="text-sm text-[var(--muted)] hover:text-white transition"
              >
                Need help?
              </a>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-10">{children}</main>
          <footer className="mx-auto max-w-6xl px-4 pb-10 text-sm text-[var(--muted)]">
            Built for productivity — Daisler Print
          </footer>
        </div>
      </body>
    </html>
  );
}
