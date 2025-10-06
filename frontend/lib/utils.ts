import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

import type { LineRange } from "./types"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function computeChangedLineRanges(
  previous: string,
  next: string
): LineRange[] {
  const previousLines = previous.split(/\r?\n/)
  const nextLines = next.split(/\r?\n/)

  const m = previousLines.length
  const n = nextLines.length
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    new Array<number>(n + 1).fill(0)
  )

  for (let i = m - 1; i >= 0; i -= 1) {
    for (let j = n - 1; j >= 0; j -= 1) {
      if (previousLines[i] === nextLines[j]) {
        dp[i][j] = dp[i + 1][j + 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
      }
    }
  }

  const changed = new Set<number>()
  let i = 0
  let j = 0

  while (i < m && j < n) {
    if (previousLines[i] === nextLines[j]) {
      i += 1
      j += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i += 1
    } else {
      changed.add(j + 1)
      j += 1
    }
  }

  while (j < n) {
    changed.add(j + 1)
    j += 1
  }

  const sorted = Array.from(changed).sort((a, b) => a - b)
  const ranges: LineRange[] = []

  let currentStart: number | null = null
  let currentEnd: number | null = null

  for (const line of sorted) {
    if (currentStart === null) {
      currentStart = line
      currentEnd = line
      continue
    }

    if (line === (currentEnd as number) + 1) {
      currentEnd = line
    } else {
      ranges.push({ start: currentStart, end: currentEnd as number })
      currentStart = line
      currentEnd = line
    }
  }

  if (currentStart !== null) {
    ranges.push({ start: currentStart, end: currentEnd as number })
  }

  return ranges
}
