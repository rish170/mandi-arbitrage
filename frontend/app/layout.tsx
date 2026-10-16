import type { Metadata } from "next";
import "./globals.css";
import {
  fraunces,
  hankenGrotesk,
  notoSansDevanagari,
  notoSerifDevanagari,
} from "@/lib/fonts";
import { ThemeProvider } from "@/components/theme-provider";
import { I18nProvider } from "@/lib/i18n";
import { ParticlesBackground } from "@/components/ParticlesBackground";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "Mandi Arbitrage Advisor | मंडी भाव सलाहकार",
  description:
    "Find your highest net profit after transport and statutory deductions across nearby APMC mandis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${fraunces.variable} ${hankenGrotesk.variable} ${notoSansDevanagari.variable} ${notoSerifDevanagari.variable}`}
    >
      <body className="antialiased min-h-screen flex flex-col relative selection:bg-forest selection:text-white dark:selection:bg-forest-strong dark:selection:text-black">
        <ThemeProvider>
          <I18nProvider>
            <ParticlesBackground />
            <Navbar />
            <main className="flex-1 w-full max-w-5xl mx-auto px-4 pt-24 pb-16 flex flex-col">
              {children}
            </main>
            <Footer />
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
