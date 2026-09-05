/**
 * Andromeda-derived mission-control primitives.
 *
 * These components borrow their *mechanics* and layout from the Andromeda
 * design system (MIT, https://github.com/uiNerd16/aicanvas — Copyright (c)
 * 2026 AI Canvas). They are written against this app's own conventions
 * (`cn`, `cva`, `motion/react`, the `@/lib/icons` barrel) and, crucially,
 * against the Indagis palette rather than Andromeda's hardcoded dark-only
 * hex values — see ./tokens for that bridge. The upstream visual identity is
 * therefore borrowed in structure, not in colour: these read correctly in
 * both the light and dark themes.
 */

export { Alert, type AlertProps, type AlertVariant } from './alert'
export { CornerMarkers, type CornerMarkersProps } from './corner-markers'
export { type Column, DataTable, type DataTableProps } from './data-table'
export { HeatGrid, type HeatGridProps, type HeatTone } from './heat-grid'
export { Kicker, Panel, PanelHeader, type PanelHeaderProps, type PanelProps } from './panel'
export { RadarChart, type RadarChartProps, type RadarSeries } from './radar-chart'
export { StatTile, type StatTileProps, type StatTone } from './stat-tile'
export { StatusBar, type StatusBarProps, type StatusBarTone } from './status-bar'
export { tokens as andromedaTokens } from './tokens'
export { TrendChart, type TrendChartProps, type TrendSeries } from './trend-chart'
