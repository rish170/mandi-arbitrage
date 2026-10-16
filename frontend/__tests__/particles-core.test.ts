import { describe, it, expect } from "vitest";
import {
  calculateDensityCount,
  createParticle,
  calculateRepulse,
  calculateGrab,
  updateParticlePosition,
  computeDistance,
} from "@/lib/particles-core";

describe("Particles Core Logic", () => {
  it("calculates particle density according to area and config", () => {
    // 1200 x 800 area = 960 * 1000
    // (960 * 70) / 900 ~ 75
    const count = calculateDensityCount(1200, 800, 70, 900, false);
    expect(count).toBeGreaterThan(50);
    expect(count).toBeLessThan(100);
  });

  it("strictly enforces mobile cap of 40 particles on mobile viewports (<768px)", () => {
    const mobileCount = calculateDensityCount(375, 812, 70, 900, true);
    expect(mobileCount).toBeLessThanOrEqual(40);

    const boundaryMobileCount = calculateDensityCount(767, 1000, 100, 500, false);
    expect(boundaryMobileCount).toBeLessThanOrEqual(40);
  });

  it("handles zero or negative dimensions safely", () => {
    expect(calculateDensityCount(0, 0)).toBe(0);
    expect(calculateDensityCount(-100, 500)).toBe(0);
  });

  it("creates a particle with valid initial coordinates and velocities", () => {
    const p = createParticle(1, 800, 600, 1.2, 3, true, 0.5, true);
    expect(p.id).toBe(1);
    expect(p.x).toBeGreaterThanOrEqual(0);
    expect(p.x).toBeLessThanOrEqual(800);
    expect(p.y).toBeGreaterThanOrEqual(0);
    expect(p.y).toBeLessThanOrEqual(600);
    expect(p.radius).toBeGreaterThan(0);
    expect(p.opacity).toBeGreaterThan(0);
  });

  it("calculates repulse displacement when mouse is within repulse radius", () => {
    // Particle at (100, 100), mouse at (105, 100) -> distance 5 < 110
    const { dx, dy, repulsed } = calculateRepulse(100, 100, 105, 100, 110, 8);
    expect(repulsed).toBe(true);
    expect(dx).toBeLessThan(0); // Pushed to the left away from mouse
    expect(dy).toBeCloseTo(0, 5);
  });

  it("returns zero displacement when mouse is outside repulse radius", () => {
    // Particle at (100, 100), mouse at (300, 300) -> distance ~ 282 > 110
    const { dx, dy, repulsed } = calculateRepulse(100, 100, 300, 300, 110, 8);
    expect(repulsed).toBe(false);
    expect(dx).toBe(0);
    expect(dy).toBe(0);
  });

  it("handles null mouse coordinates gracefully without repulse", () => {
    const res = calculateRepulse(100, 100, null, null, 110);
    expect(res.repulsed).toBe(false);
    expect(res.dx).toBe(0);
    expect(res.dy).toBe(0);
  });

  it("calculates grab line alpha when mouse is within grab distance", () => {
    // Particle at (100, 100), mouse at (170, 100) -> distance 70 <= 140
    const res = calculateGrab(100, 100, 170, 100, 140, 1.0);
    expect(res.grabbed).toBe(true);
    expect(res.distance).toBe(70);
    expect(res.alpha).toBeCloseTo(0.5, 5);
  });

  it("returns grabbed: false and zero alpha when mouse is outside grab distance", () => {
    // Particle at (100, 100), mouse at (300, 100) -> distance 200 > 140
    const res = calculateGrab(100, 100, 300, 100, 140, 1.0);
    expect(res.grabbed).toBe(false);
    expect(res.alpha).toBe(0);
    expect(res.distance).toBe(200);
  });

  it("handles null mouse coordinates gracefully without grabbing", () => {
    const res = calculateGrab(100, 100, null, null, 140);
    expect(res.grabbed).toBe(false);
    expect(res.alpha).toBe(0);
    expect(res.distance).toBe(0);
  });

  it("updates particle position and wraps boundaries in out_mode", () => {
    const p = {
      id: 1,
      x: 799,
      y: 300,
      vx: 10,
      vy: 0,
      radius: 3,
      baseRadius: 3,
      opacity: 0.5,
    };
    const nextP = updateParticlePosition(p, 800, 600, "out");
    expect(nextP.x).toBe(-3); // Wrapped to negative radius
  });

  it("computes exact Euclidean distance between two points", () => {
    const dist = computeDistance(0, 0, 30, 40);
    expect(dist).toBe(50);
  });
});
