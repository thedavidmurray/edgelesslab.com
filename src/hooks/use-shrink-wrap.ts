"use client";

import { useMemo } from "react";
import { usePreText } from "@/hooks/use-pretext";

/**
 * Finds the tightest container width that preserves the original line count.
 *
 * Uses walkLineRanges to find the widest line at full width, then verifies
 * that shrinking to that width doesn't increase the line count. The result
 * is a perfectly balanced paragraph with no wasted trailing whitespace.
 *
 * CSS text-wrap: balance is a heuristic. This is mathematically exact.
 *
 * Pure PreText math (no DOM reads), so it is computed during render via
 * useMemo rather than an effect + setState round-trip.
 */
export function useShrinkWrap(
  text: string,
  font: string,
  lineHeight: number,
  maxWidth: number
): number | null {
  const { ready, prepare, layout, prepareWithSegments, walkLineRanges } =
    usePreText("Geist");

  return useMemo(() => {
    if (
      !ready ||
      !prepare ||
      !layout ||
      !prepareWithSegments ||
      !walkLineRanges ||
      maxWidth <= 0
    )
      return null;

    // Get baseline line count at full width
    const prepared = prepare(text, font);
    if (!prepared) return null;
    const baseline = layout(prepared, maxWidth, lineHeight);
    if (!baseline || baseline.lineCount <= 1) {
      // Single line: shrink-wrap to actual text width
      const segmented = prepareWithSegments(text, font);
      if (!segmented) return null;
      let maxLineWidth = 0;
      walkLineRanges(segmented, maxWidth, (line) => {
        if (line.width > maxLineWidth) maxLineWidth = line.width;
      });
      return Math.ceil(maxLineWidth);
    }

    // Multi-line: find the widest line
    const segmented = prepareWithSegments(text, font);
    if (!segmented) return null;
    let maxLineWidth = 0;
    walkLineRanges(segmented, maxWidth, (line) => {
      if (line.width > maxLineWidth) maxLineWidth = line.width;
    });

    // The tightest width is the widest line, rounded up
    let candidate = Math.ceil(maxLineWidth);

    // Verify line count is preserved (edge case: rounding may cause reflow)
    const check = layout(prepared, candidate, lineHeight);
    if (check && check.lineCount > baseline.lineCount) {
      // Add pixels until line count matches
      while (candidate < maxWidth) {
        candidate++;
        const recheck = layout(prepared, candidate, lineHeight);
        if (recheck && recheck.lineCount <= baseline.lineCount) break;
      }
    }

    return candidate;
  }, [
    ready,
    text,
    font,
    lineHeight,
    maxWidth,
    prepare,
    layout,
    prepareWithSegments,
    walkLineRanges,
  ]);
}
