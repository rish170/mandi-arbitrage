import {
  Fraunces,
  Hanken_Grotesk,
  Noto_Sans_Devanagari,
  Noto_Serif_Devanagari,
} from "next/font/google";

export const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

export const hankenGrotesk = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-hanken",
  display: "swap",
});

export const notoSansDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari", "latin"],
  variable: "--font-noto-sans-devanagari",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const notoSerifDevanagari = Noto_Serif_Devanagari({
  subsets: ["devanagari", "latin"],
  variable: "--font-noto-serif-devanagari",
  display: "swap",
  weight: ["400", "600", "700"],
});
