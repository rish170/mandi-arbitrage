export interface ParticleState {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  baseRadius: number;
  opacity: number;
}

export interface MousePosition {
  x: number | null;
  y: number | null;
}

/**
 * Calculates the number of particles based on viewport area and config density.
 * Strictly caps particles at 40 on mobile viewports (< 768px).
 */
export function calculateDensityCount(
  width: number,
  height: number,
  value: number = 70,
  valueArea: number = 900,
  isMobile: boolean = false
): number {
  if (width <= 0 || height <= 0) return 0;
  const area = (width * height) / 1000;
  const rawCount = Math.round((area * value) / valueArea);
  const boundedCount = Math.max(5, rawCount);

  if (isMobile || width < 768) {
    return Math.min(boundedCount, 40);
  }
  return boundedCount;
}

/**
 * Creates an initial particle state with randomized positions and velocities.
 */
export function createParticle(
  id: number,
  width: number,
  height: number,
  speed: number = 1.2,
  sizeValue: number = 3,
  sizeRandom: boolean = true,
  opacityValue: number = 0.5,
  opacityRandom: boolean = true
): ParticleState {
  const angle = Math.random() * Math.PI * 2;
  const velocityMagnitude = (Math.random() * 0.5 + 0.5) * speed;

  const radius = sizeRandom
    ? Math.max(1, Math.random() * sizeValue)
    : sizeValue;

  const opacity = opacityRandom
    ? Math.max(0.15, Math.random() * opacityValue)
    : opacityValue;

  return {
    id,
    x: Math.random() * width,
    y: Math.random() * height,
    vx: Math.cos(angle) * velocityMagnitude,
    vy: Math.sin(angle) * velocityMagnitude,
    radius,
    baseRadius: radius,
    opacity,
  };
}

/**
 * Pure repulse calculation. When mouse is within repulseDistance, computes displacement vector.
 */
export function calculateRepulse(
  px: number,
  py: number,
  mx: number | null,
  my: number | null,
  repulseDistance: number = 110,
  maxForce: number = 8
): { dx: number; dy: number; repulsed: boolean } {
  if (mx === null || my === null) {
    return { dx: 0, dy: 0, repulsed: false };
  }

  const dx = px - mx;
  const dy = py - my;
  const dist = Math.hypot(dx, dy);

  if (dist > 0 && dist < repulseDistance) {
    const forceRatio = 1 - dist / repulseDistance;
    const force = forceRatio * maxForce;
    const nx = (dx / dist) * force;
    const ny = (dy / dist) * force;
    return { dx: nx, dy: ny, repulsed: true };
  }

  return { dx: 0, dy: 0, repulsed: false };
}

/**
 * Pure grab calculation.
 * When mouse is within grabDistance, computes whether the particle is grabbed and the line alpha.
 */
export function calculateGrab(
  px: number,
  py: number,
  mx: number | null,
  my: number | null,
  grabDistance: number = 140,
  maxOpacity: number = 1.0
): { grabbed: boolean; alpha: number; distance: number } {
  if (mx === null || my === null) {
    return { grabbed: false, alpha: 0, distance: 0 };
  }

  const dist = Math.hypot(px - mx, py - my);
  if (dist > 0 && dist <= grabDistance) {
    const alpha = (1 - dist / grabDistance) * maxOpacity;
    return { grabbed: true, alpha, distance: dist };
  }

  return { grabbed: false, alpha: 0, distance: dist };
}

/**
 * Updates a particle's position and wraps edges when out_mode is "out".
 */
export function updateParticlePosition(
  particle: ParticleState,
  width: number,
  height: number,
  outMode: string = "out"
): ParticleState {
  let nextX = particle.x + particle.vx;
  let nextY = particle.y + particle.vy;

  if (outMode === "out") {
    if (nextX < -particle.radius) {
      nextX = width + particle.radius;
    } else if (nextX > width + particle.radius) {
      nextX = -particle.radius;
    }

    if (nextY < -particle.radius) {
      nextY = height + particle.radius;
    } else if (nextY > height + particle.radius) {
      nextY = -particle.radius;
    }
  }

  return {
    ...particle,
    x: nextX,
    y: nextY,
  };
}

/**
 * Computes Euclidean distance between two points.
 */
export function computeDistance(
  x1: number,
  y1: number,
  x2: number,
  y2: number
): number {
  return Math.hypot(x2 - x1, y2 - y1);
}
