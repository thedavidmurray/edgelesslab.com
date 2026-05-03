"use client";

import { useRef, useEffect, useCallback, useState } from "react";

/**
 * Hero background combining looping ASCII demo videos with
 * real-time particle attractor canvas overlay.
 * Randomly picks a video clip each visit. Particles add live dynamism.
 */

const VIDEO_CLIPS = [
  "/video/ascii-emergence.mp4",
  "/video/ascii-vortex.mp4",
];

type AttractorType = "lorenz" | "rossler" | "spiral" | "flow";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
}

function mulberry32(a: number) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const ATTRACTOR_TYPES: AttractorType[] = ["lorenz", "rossler", "spiral", "flow"];

function createParticles(
  count: number,
  width: number,
  height: number,
  rng: () => number
): Particle[] {
  return Array.from({ length: count }, () => ({
    x: rng() * width,
    y: rng() * height,
    vx: (rng() - 0.5) * 1.5,
    vy: (rng() - 0.5) * 1.5,
    life: Math.floor(rng() * 200) + 100,
    maxLife: 300,
  }));
}

function stepParticle(
  p: Particle,
  type: AttractorType,
  cx1: number,
  cy1: number,
  cx2: number,
  cy2: number,
  strength: number,
  seed: number,
  width: number,
  height: number,
  rng: () => number
) {
  let ax = 0,
    ay = 0;

  switch (type) {
    case "lorenz": {
      const dx1 = cx1 - p.x, dy1 = cy1 - p.y;
      const dx2 = cx2 - p.x, dy2 = cy2 - p.y;
      const d1 = Math.sqrt(dx1 * dx1 + dy1 * dy1) + 1;
      const d2 = Math.sqrt(dx2 * dx2 + dy2 * dy2) + 1;
      ax = (dx1 / d1 - dy2 / d2) * strength;
      ay = (dy1 / d1 + dx2 / d2) * strength;
      break;
    }
    case "rossler": {
      const dx = cx1 - p.x, dy = cy1 - p.y;
      const d = Math.sqrt(dx * dx + dy * dy) + 1;
      ax = (-dy / d + dx * 0.008) * strength;
      ay = (dx / d + dy * 0.008) * strength;
      break;
    }
    case "spiral": {
      const dx = cx1 - p.x, dy = cy1 - p.y;
      const d = Math.sqrt(dx * dx + dy * dy) + 1;
      const angle = Math.atan2(dy, dx) + 0.4;
      ax = ((Math.cos(angle) / d) * strength * 8);
      ay = ((Math.sin(angle) / d) * strength * 8);
      break;
    }
    case "flow": {
      ax = Math.sin(p.y * 0.003 + seed * 0.01) * strength * 0.8;
      ay = Math.cos(p.x * 0.003 + seed * 0.01) * strength * 0.8;
      break;
    }
  }

  p.vx += ax;
  p.vy += ay;
  p.vx *= 0.985;
  p.vy *= 0.985;
  p.x += p.vx;
  p.y += p.vy;
  p.life--;

  if (p.life <= 0) {
    p.x = rng() * width;
    p.y = rng() * height;
    p.vx = (rng() - 0.5) * 1.5;
    p.vy = (rng() - 0.5) * 1.5;
    p.life = Math.floor(rng() * 200) + 100;
  }

  if (p.x < 0) p.x += width;
  if (p.x >= width) p.x -= width;
  if (p.y < 0) p.y += height;
  if (p.y >= height) p.y -= height;
}

const COLORS: Record<AttractorType, [number, number, number]> = {
  lorenz: [129, 140, 248],
  rossler: [52, 211, 153],
  spiral: [167, 139, 250],
  flow: [96, 165, 250],
};

export function GenerativeHeroBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const stateRef = useRef<{
    particles: Particle[];
    type: AttractorType;
    seed: number;
    rng: () => number;
    cx1: number; cy1: number; cx2: number; cy2: number;
    strength: number;
  } | null>(null);

  // Pick a random clip on mount
  const [clipSrc] = useState(
    () => VIDEO_CLIPS[Math.floor(Math.random() * VIDEO_CLIPS.length)]
  );

  const init = useCallback((canvas: HTMLCanvasElement) => {
    const seed = (Date.now() ^ (Math.random() * 0xffffffff)) >>> 0;
    const rng = mulberry32(seed);
    const type = ATTRACTOR_TYPES[Math.floor(rng() * ATTRACTOR_TYPES.length)];
    const w = canvas.width;
    const h = canvas.height;

    stateRef.current = {
      particles: createParticles(150, w, h, rng),
      type, seed, rng,
      cx1: w * (0.3 + rng() * 0.4),
      cy1: h * (0.3 + rng() * 0.4),
      cx2: w * (0.3 + rng() * 0.4),
      cy2: h * (0.3 + rng() * 0.4),
      strength: 0.015 + rng() * 0.02,
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      init(canvas);
    };

    resize();

    const draw = () => {
      const state = stateRef.current;
      if (!state || !canvas) return;

      const w = canvas.getBoundingClientRect().width;
      const h = canvas.getBoundingClientRect().height;
      const color = COLORS[state.type];

      ctx.fillStyle = "rgba(0, 0, 0, 0.04)";
      ctx.fillRect(0, 0, w, h);

      for (const p of state.particles) {
        stepParticle(
          p, state.type,
          state.cx1, state.cy1, state.cx2, state.cy2,
          state.strength, state.seed,
          canvas.width, canvas.height, state.rng
        );

        const alpha = (p.life / p.maxLife) * 0.4;
        const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
        const size = 1 + speed * 0.3;

        ctx.beginPath();
        ctx.arc(
          (p.x / canvas.width) * w,
          (p.y / canvas.height) * h,
          size, 0, Math.PI * 2
        );
        ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${alpha})`;
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);

    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [init]);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* Grid lines */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
        }}
      />
      {/* ASCII demo video -- looping, muted, covers full hero */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover opacity-30"
        style={{ mixBlendMode: "screen" }}
        src={clipSrc}
      />
      {/* Particle canvas overlay -- subtle live layer on top of video */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-30"
        style={{ mixBlendMode: "screen" }}
      />
      {/* Vignette for text readability */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 40%, transparent 0%, rgba(0,0,0,0.7) 100%)",
        }}
      />
    </div>
  );
}
