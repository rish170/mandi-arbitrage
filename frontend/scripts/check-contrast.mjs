// WCAG contrast validator for theme tokens
const tokens = {
  light: {
    bg: "#FFFFFF",
    ink: "#1B2A1F",
    inkMuted: "#56685A",
    forest: "#1F5C3B",
    forestStrong: "#174A2F",
    wheat: "#C9962B",
    wheatInk: "#8A6414",
    clay: "#B4532A",
    soil: "#6B4F3A",
  },
  dark: {
    bg: "#000000",
    ink: "#EAF2E8",
    inkMuted: "#97A89B",
    forest: "#58B874",
    forestStrong: "#7CCF94",
    wheat: "#E2B54F",
    wheatInk: "#E2B54F",
    clay: "#E0805A",
    soil: "#A98B72",
  },
};

function hexToRgb(hex) {
  const sanitized = hex.replace("#", "");
  const num = parseInt(sanitized, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  };
}

function getLuminance({ r, g, b }) {
  const [sR, sG, sB] = [r, g, b].map((val) => {
    const s = val / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * sR + 0.7152 * sG + 0.0722 * sB;
}

function getContrast(hex1, hex2) {
  const lum1 = getLuminance(hexToRgb(hex1));
  const lum2 = getLuminance(hexToRgb(hex2));
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

let passed = true;

for (const theme of ["light", "dark"]) {
  const t = tokens[theme];
  const textPairs = [
    { name: "ink on bg", fg: t.ink, bg: t.bg, min: 4.5 },
    { name: "inkMuted on bg", fg: t.inkMuted, bg: t.bg, min: 4.5 },
    { name: "wheatInk on bg", fg: t.wheatInk, bg: t.bg, min: 4.5 },
    { name: "forest on bg (UI)", fg: t.forest, bg: t.bg, min: 3.0 },
    { name: "clay on bg (UI)", fg: t.clay, bg: t.bg, min: 3.0 },
  ];

  console.log(`\nChecking WCAG contrast for ${theme.toUpperCase()} theme:`);
  for (const pair of textPairs) {
    const cr = getContrast(pair.fg, pair.bg);
    const ok = cr >= pair.min;
    console.log(
      `  ${ok ? "PASS" : "FAIL"}: ${pair.name} - Ratio: ${cr.toFixed(2)}:1 (Required: ${pair.min}:1)`
    );
    if (!ok) passed = false;
  }
}

if (!passed) {
  console.error("\nContrast check FAILED!");
  process.exit(1);
} else {
  console.log("\nAll WCAG contrast checks PASSED.");
}
