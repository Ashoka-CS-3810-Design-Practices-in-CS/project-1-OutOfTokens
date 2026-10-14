import { Tabs } from '@heroui/react'
import type { Key } from '@heroui/react'
import type { RouteMode } from '../types'

interface RouteModeTabsProps {
  value: RouteMode
  onChange: (mode: RouteMode) => void
}

const modes: { id: RouteMode; label: string }[] = [
  { id: 'fastest', label: 'Fastest' },
  { id: 'fewest_stations', label: 'Minimum stations' },
  { id: 'fewest_interchanges', label: 'Minimum interchanges' },
]

// picks what the route should be optimised for
export default function RouteModeTabs({ value, onChange }: RouteModeTabsProps) {
  return (
    <Tabs
      className="route-mode-tabs w-full"
      variant="secondary"
      selectedKey={value}
      onSelectionChange={(key: Key) => onChange(key as RouteMode)}
    >
      <Tabs.ListContainer>
        <Tabs.List aria-label="Route preference">
          {modes.map((mode) => (
            <Tabs.Tab key={mode.id} id={mode.id}>
              {mode.label}
              <Tabs.Indicator />
            </Tabs.Tab>
          ))}
        </Tabs.List>
      </Tabs.ListContainer>
    </Tabs>
  )
}
