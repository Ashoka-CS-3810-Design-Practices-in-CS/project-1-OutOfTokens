import MetroMap from './components/MetroMap'

export default function App() {
  return (
    <div className="app">
      <aside className="panel">
        <h1>Delhi Metro Route Planner</h1>
        <p className="panel-note">Station search and routes will appear here.</p>
      </aside>
      <main className="map-area">
        <MetroMap />
        <p className="map-credit">Map data © OpenStreetMap contributors</p>
      </main>
    </div>
  )
}
