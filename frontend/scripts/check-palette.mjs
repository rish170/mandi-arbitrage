// Palette check: Enforces NO hues between 190 and 340 degrees anywhere
import fs from "fs";
import path from "path";

const FORBIDDEN_MIN_HUE = 190;
const FORBIDDEN_MAX_HUE = 340;

function hexToHsl(hex) {
  let c = hex.replace("#", "");
  if (c.length === 3) {
    c = c.split("").map((x) => x + x).join("");
  }
  if (c.length !== 6) return null;

  const r = parseInt(c.substring(0, 2), 16) / 255;
  const g = parseInt(c.substring(2, 4), 16) / 255;
  const b = parseInt(c.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;

  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (delta !== 0) {
    s = l > 0.5 ? delta / (2 - max - min) : delta / (max + min);
    switch (max) {
      case r:
        h = ((g - b) / delta + (g < b ? 6 : 0)) * 60;
        break;
      case g:
        h = ((b - r) / delta + 2) * 60;
        break;
      case b:
        h = ((r - g) / delta + 4) * 60;
        break;
    }
  }

  return { h, s: s * 100, l: l * 100 };
}

const HEX_REGEX = /#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g;

function scanDir(dir, errors) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (
        [
          "node_modules",
          ".next",
          ".git",
          "coverage",
          "dist",
          "scripts",
        ].includes(entry.name)
      ) {
        continue;
      }
      scanDir(fullPath, errors);
    } else if (
      entry.isFile() &&
      /\.(tsx|ts|jsx|js|css|json)$/.test(entry.name)
    ) {
      const content = fs.readFileSync(fullPath, "utf-8");
      const lines = content.split("\n");
      lines.forEach((line, lineIdx) => {
        let match;
        while ((match = HEX_REGEX.exec(line)) !== null) {
          const hex = match[0];
          const hsl = hexToHsl(hex);
          if (hsl && hsl.s >= 8) {
            // Ignore low-saturation neutrals
            if (hsl.h >= FORBIDDEN_MIN_HUE && hsl.h <= FORBIDDEN_MAX_HUE) {
              errors.push({
                file: fullPath,
                line: lineIdx + 1,
                hex,
                hue: Math.round(hsl.h),
                saturation: Math.round(hsl.s),
              });
            }
          }
        }
      });
    }
  }
}

const errors = [];
scanDir(process.cwd(), errors);

if (errors.length > 0) {
  console.error(
    `\nPalette check FAILED: Found ${errors.length} forbidden colors (hue between 190° and 340°):`
  );
  errors.forEach((e) => {
    console.error(
      `  ${e.file}:${e.line} -> ${e.hex} (Hue: ${e.hue}°, Saturation: ${e.saturation}%)`
    );
  });
  process.exit(1);
} else {
  console.log("\nPalette check PASSED: No forbidden hues (190° - 340°) found.");
}
