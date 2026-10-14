import { Autocomplete, EmptyState, Label, ListBox, SearchField, useFilter } from '@heroui/react'
import type { Key } from '@heroui/react'
import type { Line, Station } from '../types'

interface StationSearchProps {
  label: string
  placeholder: string
  stations: Station[]
  lines: Map<string, Line>
  value: string | null
  onChange: (stationId: string | null) => void
  // the station picked in the other field, so the same one can't be chosen twice
  excludeId?: string | null
}

// a searchable list of stations; a station can only be chosen from the list
export default function StationSearch({
  label,
  placeholder,
  stations,
  lines,
  value,
  onChange,
  excludeId,
}: StationSearchProps) {
  // "base" ignores case and accents, so "rajiv" finds "Rajiv Chowk"
  const { contains } = useFilter({ sensitivity: 'base' })

  return (
    <Autocomplete
      className="station-search"
      fullWidth
      placeholder={placeholder}
      selectionMode="single"
      value={value}
      onChange={(key: Key | null) => onChange(key === null ? null : String(key))}
      disabledKeys={excludeId ? [excludeId] : []}
    >
      <Label>{label}</Label>
      <Autocomplete.Trigger>
        <Autocomplete.Value />
        <Autocomplete.ClearButton />
        <Autocomplete.Indicator />
      </Autocomplete.Trigger>
      <Autocomplete.Popover>
        <Autocomplete.Filter filter={contains}>
          <SearchField autoFocus name="search" aria-label={`Search ${label.toLowerCase()} station`}>
            <SearchField.Group>
              <SearchField.SearchIcon />
              <SearchField.Input placeholder="Type a station name" />
              <SearchField.ClearButton />
            </SearchField.Group>
          </SearchField>
          <ListBox renderEmptyState={() => <EmptyState>No station matches that name</EmptyState>}>
            {stations.map((station) => (
              <ListBox.Item key={station.id} id={station.id} textValue={station.name}>
                <span className="station-option">
                  <span className="station-option-name">{station.name}</span>
                  <LineDots lineIds={station.lines} lines={lines} />
                </span>
                <ListBox.ItemIndicator />
              </ListBox.Item>
            ))}
          </ListBox>
        </Autocomplete.Filter>
      </Autocomplete.Popover>
    </Autocomplete>
  )
}

// one coloured dot per line at the station (branch lines share a colour, so show each colour once)
function LineDots({ lineIds, lines }: { lineIds: string[]; lines: Map<string, Line> }) {
  const shown = new Map<string, string>()
  for (const id of lineIds) {
    const line = lines.get(id)
    if (line && !shown.has(line.colour)) shown.set(line.colour, line.name)
  }
  return (
    <span className="line-dots">
      {[...shown].map(([colour, name]) => (
        <span key={colour} className="line-dot" style={{ background: colour }} title={name} />
      ))}
    </span>
  )
}
