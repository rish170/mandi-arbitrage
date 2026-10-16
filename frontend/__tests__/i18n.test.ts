import { describe, it, expect } from "vitest";
import en from "@/locales/en.json";
import hi from "@/locales/hi.json";

function getDeepKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  let keys: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullPath = prefix ? `${prefix}.${key}` : key;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      keys = keys.concat(getDeepKeys(value as Record<string, unknown>, fullPath));
    } else {
      keys.push(fullPath);
    }
  }
  return keys.sort();
}

describe("i18n Locale Parity", () => {
  it("en.json and hi.json have identical key sets", () => {
    const enKeys = getDeepKeys(en);
    const hiKeys = getDeepKeys(hi);

    const missingInHi = enKeys.filter((k) => !hiKeys.includes(k));
    const missingInEn = hiKeys.filter((k) => !enKeys.includes(k));

    expect(
      missingInHi,
      `Keys present in en.json but missing in hi.json: ${missingInHi.join(", ")}`
    ).toEqual([]);

    expect(
      missingInEn,
      `Keys present in hi.json but missing in en.json: ${missingInEn.join(", ")}`
    ).toEqual([]);

    expect(enKeys).toEqual(hiKeys);
  });

  it("all translation values in both locales are non-empty strings", () => {
    const checkValues = (obj: Record<string, unknown>, localeName: string) => {
      for (const [key, val] of Object.entries(obj)) {
        if (typeof val === "object" && val !== null) {
          checkValues(val as Record<string, unknown>, localeName);
        } else {
          expect(
            typeof val,
            `${localeName} key "${key}" must be a string`
          ).toBe("string");
          expect(
            (val as string).trim().length,
            `${localeName} key "${key}" must not be empty`
          ).toBeGreaterThan(0);
        }
      }
    };

    checkValues(en, "en.json");
    checkValues(hi, "hi.json");
  });

  it("translates all required MVP crops to accurate everyday Hindi", () => {
    expect(hi.crops.wheat).toBe("गेहूं");
    expect(hi.crops.rice).toContain("चावल");
    expect(hi.crops.soyabean).toBe("सोयाबीन");
    expect(hi.crops.cotton).toBe("कपास");
    expect(hi.crops.onion).toBe("प्याज");
    expect(hi.crops.potato).toBe("आलू");
    expect(hi.crops.tomato).toBe("टमाटर");
  });
});
