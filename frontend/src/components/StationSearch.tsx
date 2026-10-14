import { Autocomplete, EmptyState, Label, ListBox, SearchField } from '@heroui/react'
import type { Key } from '@heroui/react'
import { useRef, useState } from 'react'
import { MESSAGES } from '../messages'
import { MAX_QUERY_LENGTH } from '../stationIndex'
import type { Line } from '../types'
import { useRouteStore } from '../useRouteStore'

interface StationSearchProps {
  label: string
  placeholder: string
  value: string | null
  onChange: (stationId: string | null) => void
  // the station picked in the other field; choosing it here is refused with ER3
  otherId: string | null
}

// a search box with up to 8 suggestions; a station can only be set by choosing one
export default function StationSearch({ label, placeholder, value, onChange, otherId }: StationSearchProps) {
  const index = useRouteStore((s) => s.index)
  const lines = useRouteStore((s) => s.linesById)
  const [query, setQuery] = useState('')
  const [error, setError] = useState<string | null>(null)
  // set when a suggestion is picked, so closing the list afterwards isn't treated as "typed but didn't choose"
  const chose = useRef(false)

  // Reset (or anything else) clearing the station also clears this field's message
  const [prevValue, setPrevValue] = useState(value)
  if (value !== prevValue) {
    setPrevValue(value)
    if (value === null) setError(null)
  }

  const suggestions = index?.search(query) ?? []
  const selected = value ? index?.get(value) : undefined

  function choose(key: Key | null) {
    chose.current = true
    if (key === null) {
      setError(null)
      onChange(null)
      return
    }
    const id = String(key)
    if (id === otherId) {
      setError(MESSAGES.sameStation) // ER3: the field keeps its current station
      return
    }
    setError(null)
    onChange(id)
  }

  function openChange(isOpen: boolean) {
    if (isOpen) {
      chose.current = false
      return
    }
    // ER2: text was typed but no suggestion chosen
    if (!chose.current && query.trim()) setError(MESSAGES.chooseFromList)
    setQuery('')
  }

  return (
    <div className="station-search-field">
      <Autocomplete
        className="station-search"
        fullWidth
        placeholder={placeholder}
        selectionMode="single"
        value={value}
        onChange={choose}
        onClear={() => choose(null)}
        onOpenChange={openChange}
        isInvalid={error !== null}
        isDisabled={!index}
      >
        <Label>{label}</Label>
        <Autocomplete.Trigger>
          {/* the name comes from the index, since the chosen station may not be in the current suggestions */}
          <Autocomplete.Value>{() => selected?.name ?? placeholder}</Autocomplete.Value>
          <Autocomplete.ClearButton />
          <Autocomplete.Indicator />
        </Autocomplete.Trigger>
        <Autocomplete.Popover>
          <Autocomplete.Filter inputValue={query} onInputChange={setQuery}>
            <SearchField autoFocus name="search" aria-label={`Search ${label.toLowerCase()} station`}>
              <SearchField.Group>
                <SearchField.SearchIcon />
                <SearchField.Input placeholder="Type a station name" maxLength={MAX_QUERY_LENGTH} />
                <SearchField.ClearButton />
              </SearchField.Group>
            </SearchField>
            <ListBox
              renderEmptyState={() => (
                <EmptyState>{query.trim() ? MESSAGES.noMatch : 'Start typing a station name'}</EmptyState>
              )}
            >
              {suggestions.map((station) => (
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
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
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
