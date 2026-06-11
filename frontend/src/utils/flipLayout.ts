/** Panel layout ratios — mirrored by backend compute_flip_layout(). */

export const FLIP_PANEL_WIDTH_RATIO = 1.65
export const FLIP_PANEL_HEIGHT_RATIO = 1.4
export const FLIP_GAP_RATIO = 0.12
export const FLIP_COLON_SIZE_RATIO = 0.85
export const FLIP_COLON_MARGIN_RATIO = 0.04
export const FLIP_RADIUS_RATIO = 0.14
export const FLIP_HINGE_HEIGHT_RATIO = 0.05
export const FLIP_PERSPECTIVE_RATIO = 5

export function flipPanelWidth(fontSize: number): number {
  return fontSize * FLIP_PANEL_WIDTH_RATIO
}

export function flipPanelHeight(fontSize: number): number {
  return fontSize * FLIP_PANEL_HEIGHT_RATIO
}

export function flipGap(fontSize: number): number {
  return fontSize * FLIP_GAP_RATIO
}

export function flipColonWidth(fontSize: number): number {
  return fontSize * (FLIP_COLON_SIZE_RATIO + 2 * FLIP_COLON_MARGIN_RATIO)
}

export function flipRadius(fontSize: number): number {
  return fontSize * FLIP_RADIUS_RATIO
}
