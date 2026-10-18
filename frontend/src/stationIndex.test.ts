import { describe, expect, it } from 'vitest'
import { buildStationIndex, MAX_QUERY_LENGTH, MAX_SUGGESTIONS } from './stationIndex'
import type { Station } from './types'

function station(id: string, name: string): Station {
  return { id, name, lat: 28.6, lon: 77.2, lines: ['YELLOW'] }
}

const STATIONS = [
  station('RAJIV_CHOWK', 'Rajiv Chowk'),
  station('RAJOURI_GARDEN', 'Rajouri Garden'),
  station('CHANDNI_CHOWK', 'Chandni Chowk'),
  station('NEW_DELHI', 'New Delhi'),
  station('KASHMERE_GATE', 'Kashmere Gate'),
  station('DILLI_HAAT_INA', 'Dilli Haat INA'),
]

const names = (stations: Station[]) => stations.map((s) => s.name)

describe('station search', () => {
  const index = buildStationIndex(STATIONS)

  it('suggests nothing until something is typed', () => {
    expect(index.search('')).toEqual([])
    expect(index.search('   ')).toEqual([])
  })

  it('ignores upper and lower case and spaces around the text', () => {
    expect(names(index.search('  rAjIv '))).toEqual(['Rajiv Chowk'])
  })

  it('lists names that start with the text before names that only contain it', () => {
    // "chowk" starts no name; "ch" starts Chandni Chowk and is inside Rajiv Chowk
    expect(names(index.search('ch'))).toEqual(['Chandni Chowk', 'Rajiv Chowk'])
  })

  it('finds text in the middle of a name', () => {
    expect(names(index.search('haat'))).toEqual(['Dilli Haat INA'])
  })

  it('ignores accents', () => {
    expect(names(index.search('délhi'))).toEqual(['New Delhi'])
  })

  it('says nothing matches with an empty list, not an error', () => {
    expect(index.search('zzz')).toEqual([])
  })

  it('never suggests more than 8 stations', () => {
    const many = Array.from({ length: 20 }, (_, i) => station(`S${i}`, `Sector ${i}`))
    expect(buildStationIndex(many).search('sector')).toHaveLength(MAX_SUGGESTIONS)
    expect(MAX_SUGGESTIONS).toBe(8)
  })

  it('only reads the first 100 characters of what was typed', () => {
    // "rajiv", spaces up to 100 characters, then text that is cut off and so ignored
    const long = 'rajiv'.padEnd(MAX_QUERY_LENGTH, ' ') + 'tail'
    expect(names(index.search(long))).toEqual(['Rajiv Chowk'])
  })

  it('looks up a station by its code', () => {
    expect(index.get('NEW_DELHI')?.name).toBe('New Delhi')
    expect(index.get('NOWHERE')).toBeUndefined()
  })
})
