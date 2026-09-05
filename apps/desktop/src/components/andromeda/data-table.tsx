/**
 * DataTable — a dense, sortable table with the blueprint header treatment.
 *
 * Structure borrowed from the Andromeda design system (MIT): wide-tracked
 * uppercase mono column heads over hairline-separated rows, numerics right
 * aligned and tabular so digits line up in a column.
 *
 * Generic over the row type, so a caller keeps its own field types all the
 * way into the cell renderer instead of casting at the boundary.
 *
 * Sorting is client-side and optional (`sortable` per column). It is a real
 * `<table>` with `<th scope="col">` and `aria-sort`, so a screen reader
 * announces the column, the ordering, and any change to it — a div grid
 * would announce none of that.
 */

import { useMemo, useState } from 'react'

import { ChevronDown } from '@/lib/icons'
import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export interface Column<Row> {
  /** Stable id; also the sort key when `sortable` and no `sortValue`. */
  id: string
  header: React.ReactNode
  /** Cell body. */
  cell: (row: Row) => React.ReactNode
  /** Right-align and use tabular numerals. */
  numeric?: boolean
  sortable?: boolean
  /** Value to sort on, when the cell renders something non-comparable. */
  sortValue?: (row: Row) => number | string
  width?: string
}

export interface DataTableProps<Row> extends Omit<React.ComponentProps<'div'>, 'children'> {
  rows: Row[]
  columns: Column<Row>[]
  /** Stable React key per row. */
  rowKey: (row: Row) => string
  /** Rendered in place of the table when there are no rows. */
  empty?: React.ReactNode
  onRowClick?: (row: Row) => void
}

export function DataTable<Row>({ className, columns, empty, onRowClick, rowKey, rows, ...props }: DataTableProps<Row>) {
  const [sort, setSort] = useState<null | { desc: boolean; id: string }>(null)

  const sorted = useMemo(() => {
    if (!sort) {
      return rows
    }

    const column = columns.find(c => c.id === sort.id)

    if (!column) {
      return rows
    }

    const value = (row: Row) => column.sortValue?.(row) ?? String(column.cell(row) ?? '')

    return [...rows].sort((a, b) => {
      const [x, y] = [value(a), value(b)]
      const cmp = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))

      return sort.desc ? -cmp : cmp
    })
  }, [columns, rows, sort])

  if (rows.length === 0 && empty) {
    return <>{empty}</>
  }

  return (
    // Wide tables scroll in their own container so the page body never
    // scrolls sideways.
    <div className={cn('w-full overflow-x-auto', className)} data-slot="data-table" {...props}>
      <table className="w-full border-collapse text-left">
        <thead>
          <tr>
            {columns.map(column => {
              const active = sort?.id === column.id
              const ariaSort = active ? (sort.desc ? 'descending' : 'ascending') : 'none'

              return (
                <th
                  aria-sort={column.sortable ? ariaSort : undefined}
                  className={cn(
                    'border-b border-(--ui-stroke-secondary) px-2 py-1.5 text-[0.625rem] font-normal uppercase',
                    column.numeric && 'text-right'
                  )}
                  key={column.id}
                  scope="col"
                  style={{
                    color: tokens.color.text.muted,
                    fontFamily: tokens.typography.fontMono,
                    letterSpacing: tokens.typography.tracking.wide,
                    width: column.width
                  }}
                >
                  {column.sortable ? (
                    <button
                      className="inline-flex items-center gap-1 uppercase hover:text-(--ui-text-primary)"
                      onClick={() =>
                        setSort(current =>
                          current?.id === column.id
                            ? { desc: !current.desc, id: column.id }
                            : { desc: false, id: column.id }
                        )
                      }
                      type="button"
                    >
                      {column.header}
                      {/* One chevron, rotated — the barrel ships no up-arrow
                          variant, and adding one for a caret is not worth a
                          new export. */}
                      {active && <ChevronDown className={cn('size-3', !sort.desc && 'rotate-180')} />}
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map(row => (
            <tr
              className={cn(
                'border-b border-(--ui-stroke-quaternary) last:border-b-0',
                onRowClick && 'cursor-pointer hover:bg-(--ui-row-hover-background)'
              )}
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map(column => (
                <td
                  className={cn('px-2 py-1.5 text-[0.6875rem]', column.numeric && 'text-right tabular-nums')}
                  key={column.id}
                  style={{ color: tokens.color.text.primary }}
                >
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
