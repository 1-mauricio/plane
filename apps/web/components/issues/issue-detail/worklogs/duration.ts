/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// TS twin of plane/utils/duration.py: "90", "90m", "2h 30m", "1.5h" -> minutes, or null if invalid
export const parseDuration = (value: string): number | null => {
  const s = value.trim().toLowerCase();
  if (/^\d+$/.test(s)) return Number(s);
  const re = /(\d+(?:\.\d+)?)\s*([hm])/g;
  if (!s || s.replace(re, "").trim()) return null;
  let total = 0;
  for (const m of s.matchAll(re)) total += Number(m[1]) * (m[2] === "h" ? 60 : 1);
  return Math.round(total);
};

export const formatMinutes = (minutes: number): string => {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return [h ? `${h}h` : "", m || !h ? `${m}m` : ""].filter(Boolean).join(" ");
};
