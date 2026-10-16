"use client";

import React, { useEffect, useRef } from "react";
import { particlesConfig } from "@/particles.config";
import {
  calculateDensityCount,
  createParticle,
  calculateRepulse,
  calculateGrab,
  updateParticlePosition,
  computeDistance,
  ParticleState,
} from "@/lib/particles-core";

export function ParticlesBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number | null = null;
    let particles: ParticleState[] = [];
    let mouseX: number | null = null;
    let mouseY: number | null = null;
    let width = window.innerWidth;
    let height = window.innerHeight;

    // Cache theme colors from CSS variables
    let particleColor = "#3F9B5A";
    let particleLineColor = "rgba(63, 155, 90, 0.35)";

    const updateThemeColors = () => {
      const styles = getComputedStyle(document.documentElement);
      const pColor = styles.getPropertyValue("--particle").trim();
      const pLine = styles.getPropertyValue("--particle-line").trim();
      if (pColor) particleColor = pColor;
      if (pLine) particleLineColor = pLine;
    };

    updateThemeColors();

    // Observe theme toggle class changes on <html>
    const observer = new MutationObserver(() => {
      updateThemeColors();
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    const initCanvasSize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const targetCount = calculateDensityCount(
        width,
        height,
        particlesConfig.particles.number.value,
        particlesConfig.particles.number.density.value_area,
        width < 768
      );

      particles = [];
      for (let i = 0; i < targetCount; i++) {
        particles.push(
          createParticle(
            i,
            width,
            height,
            particlesConfig.particles.move.speed,
            particlesConfig.particles.size.value,
            particlesConfig.particles.size.random,
            particlesConfig.particles.opacity.value,
            particlesConfig.particles.opacity.random
          )
        );
      }
    };

    initCanvasSize();

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    // Window-level mouse interactivity
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const handleMouseLeave = () => {
      mouseX = null;
      mouseY = null;
    };

    const handleClick = (e: MouseEvent) => {
      if (!particlesConfig.interactivity.events.onclick.enable) return;
      const clickMode = particlesConfig.interactivity.events.onclick.mode;

      if (clickMode === "push") {
        const pushCount = particlesConfig.interactivity.modes.push.particles_nb;
        for (let i = 0; i < pushCount; i++) {
          const newParticle = createParticle(
            particles.length + i,
            width,
            height,
            particlesConfig.particles.move.speed,
            particlesConfig.particles.size.value,
            particlesConfig.particles.size.random,
            particlesConfig.particles.opacity.value,
            particlesConfig.particles.opacity.random
          );
          newParticle.x = e.clientX + (Math.random() * 20 - 10);
          newParticle.y = e.clientY + (Math.random() * 20 - 10);
          particles.push(newParticle);
        }
        // Keep within mobile/desktop ceiling
        const maxAllowed = width < 768 ? 40 : 120;
        if (particles.length > maxAllowed) {
          particles = particles.slice(particles.length - maxAllowed);
        }
      } else if (clickMode === "remove") {
        const removeCount =
          particlesConfig.interactivity.modes.remove?.particles_nb ?? 2;
        particles = particles.slice(0, Math.max(5, particles.length - removeCount));
      }
    };

    const handleResize = () => {
      initCanvasSize();
      if (prefersReducedMotion) {
        renderFrame();
      }
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    window.addEventListener("mouseleave", handleMouseLeave, { passive: true });
    window.addEventListener("click", handleClick, { passive: true });
    window.addEventListener("resize", handleResize, { passive: true });

    // Render single frame
    const renderFrame = () => {
      ctx.clearRect(0, 0, width, height);

      const lineDist = particlesConfig.particles.line_linked.distance;

      // Draw linked lines between nearby particles
      ctx.lineWidth = particlesConfig.particles.line_linked.width;
      ctx.strokeStyle = particleLineColor;

      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = computeDistance(p1.x, p1.y, p2.x, p2.y);
          if (dist < lineDist) {
            const alpha = 1 - dist / lineDist;
            ctx.globalAlpha =
              alpha * particlesConfig.particles.line_linked.opacity;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      // Mouse hover interactivity: Grab mode (lines connecting cursor to nearby particles)
      const hoverEnabled = particlesConfig.interactivity.events.onhover.enable;
      const hoverMode = particlesConfig.interactivity.events.onhover.mode;

      if (
        hoverEnabled &&
        hoverMode === "grab" &&
        mouseX !== null &&
        mouseY !== null &&
        !prefersReducedMotion
      ) {
        const grabDist = particlesConfig.interactivity.modes.grab?.distance ?? 140;
        const grabOpacity =
          particlesConfig.interactivity.modes.grab?.line_linked.opacity ?? 1;

        for (let i = 0; i < particles.length; i++) {
          const p = particles[i];
          const { grabbed, alpha } = calculateGrab(
            p.x,
            p.y,
            mouseX,
            mouseY,
            grabDist,
            grabOpacity
          );
          if (grabbed) {
            ctx.lineWidth = particlesConfig.particles.line_linked.width;
            ctx.strokeStyle = particleLineColor;
            ctx.globalAlpha = alpha;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouseX, mouseY);
            ctx.stroke();
          }
        }
      }

      // Draw particles and update positions
      for (let i = 0; i < particles.length; i++) {
        let p = particles[i];

        if (!prefersReducedMotion) {
          if (hoverEnabled && hoverMode === "repulse") {
            const repulseDist =
              particlesConfig.interactivity.modes.repulse.distance;
            const { dx, dy, repulsed } = calculateRepulse(
              p.x,
              p.y,
              mouseX,
              mouseY,
              repulseDist
            );
            if (repulsed) {
              p = { ...p, x: p.x + dx, y: p.y + dy };
            }
          }

          // Move
          p = updateParticlePosition(
            p,
            width,
            height,
            particlesConfig.particles.move.out_mode
          );
          particles[i] = p;
        }

        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = particleColor;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalAlpha = 1.0;
    };

    // Animation Loop with tab visibility handling
    const loop = () => {
      renderFrame();
      animationFrameId = requestAnimationFrame(loop);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (animationFrameId !== null) {
          cancelAnimationFrame(animationFrameId);
          animationFrameId = null;
        }
      } else {
        if (!prefersReducedMotion && animationFrameId === null) {
          animationFrameId = requestAnimationFrame(loop);
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    if (prefersReducedMotion) {
      renderFrame();
    } else {
      animationFrameId = requestAnimationFrame(loop);
    }

    return () => {
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }
      observer.disconnect();
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("click", handleClick);
      window.removeEventListener("resize", handleResize);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none -z-10"
      aria-hidden="true"
    />
  );
}
