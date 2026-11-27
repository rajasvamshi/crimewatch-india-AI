import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapboxOverlay } from '@deck.gl/mapbox';

/*
 * Dark 3D base map from OpenFreeMap (free, no key, OpenStreetMap data, OpenMapTiles schema).
 * OSM's own country borders are NOT drawn: India's outline comes from our own state layer,
 * as required for Indian government sites (Survey of India depiction).
 * If the tiles cannot load, the map keeps working with the state outlines alone.
 */
const TILES = 'https://tiles.openfreemap.org/planet';
const GLYPHS = 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf';

export const INDIA_VIEW = { center: [80.5, 22.5], zoom: 4.1, pitch: 45, bearing: -8 };

function style() {
  return {
    version: 8,
    glyphs: GLYPHS,
    sources: {
      omt: { type: 'vector', url: TILES, attribution: '© OpenStreetMap contributors · OpenFreeMap' },
      states: { type: 'geojson', data: './data/india_states.geojson' },
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': '#07090d' } },
      { id: 'water', type: 'fill', source: 'omt', 'source-layer': 'water', paint: { 'fill-color': '#0b1522' } },
      { id: 'landcover', type: 'fill', source: 'omt', 'source-layer': 'landcover', paint: { 'fill-color': '#0c1410', 'fill-opacity': 0.5 } },
      { id: 'park', type: 'fill', source: 'omt', 'source-layer': 'park', paint: { 'fill-color': '#0d1a14', 'fill-opacity': 0.6 } },
      { id: 'states-fill', type: 'fill', source: 'states', paint: { 'fill-color': '#ffffff', 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 3, 0.035, 8, 0] } },
      {
        id: 'roads-minor', type: 'line', source: 'omt', 'source-layer': 'transportation', minzoom: 11,
        filter: ['in', 'class', 'minor', 'service', 'tertiary'],
        paint: { 'line-color': '#1a2230', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.5, 16, 4] },
      },
      {
        id: 'roads-major', type: 'line', source: 'omt', 'source-layer': 'transportation', minzoom: 5,
        filter: ['in', 'class', 'motorway', 'trunk', 'primary', 'secondary'],
        paint: { 'line-color': '#263247', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.4, 16, 8] },
      },
      {
        id: 'buildings-3d', type: 'fill-extrusion', source: 'omt', 'source-layer': 'building', minzoom: 13,
        paint: {
          'fill-extrusion-color': ['interpolate', ['linear'], ['coalesce', ['get', 'render_height'], 8], 0, '#1b2330', 60, '#2a3548', 200, '#3a4a66'],
          'fill-extrusion-height': ['interpolate', ['linear'], ['zoom'], 13, 0, 14.5, ['coalesce', ['get', 'render_height'], 8]],
          'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
          'fill-extrusion-opacity': 0.9,
        },
      },
      { id: 'states-line', type: 'line', source: 'states', paint: { 'line-color': '#8a96ab', 'line-opacity': 0.45, 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.6, 8, 1.4] } },
      {
        id: 'place-labels', type: 'symbol', source: 'omt', 'source-layer': 'place', minzoom: 5,
        filter: ['in', 'class', 'city', 'town', 'suburb', 'neighbourhood'],
        layout: {
          'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']], 'text-font': ['Noto Sans Regular'],
          'text-size': ['interpolate', ['linear'], ['zoom'], 5, 10, 14, 14], 'text-max-width': 8,
        },
        paint: { 'text-color': '#9aa4b2', 'text-halo-color': '#07090d', 'text-halo-width': 1.2 },
      },
    ],
  };
}

export default function MapView({ layers, view = INDIA_VIEW, interactive = true, spin = false, onReady, flyTo }) {
  const el = useRef(null);
  const mapRef = useRef(null);
  const overlayRef = useRef(null);
  const [tilesFailed, setTilesFailed] = useState(false);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: el.current, style: style(), ...view, interactive, attributionControl: { compact: true },
      maxPitch: 75, antialias: true,
    });
    mapRef.current = map;
    if (interactive) map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');
    map.on('error', (e) => {
      if (String(e?.sourceId || e?.error?.message || '').match(/omt|openfreemap|Failed to fetch/i)) setTilesFailed(true);
    });
    const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay);
    overlayRef.current = overlay;
    let raf;
    if (spin) {
      const step = () => { map.setBearing(map.getBearing() + 0.03); raf = requestAnimationFrame(step); };
      map.once('load', step);
    }
    onReady?.(map);
    return () => { cancelAnimationFrame(raf); map.remove(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { overlayRef.current?.setProps({ layers }); }, [layers]);

  useEffect(() => {
    if (flyTo && mapRef.current) mapRef.current.flyTo({ ...flyTo, speed: 0.9, curve: 1.5, essential: true });
  }, [flyTo]);

  return (
    <>
      <div ref={el} className="map" style={{ position: 'absolute', inset: 0 }} role="application" aria-label="Map of reported incidents in India" />
      {tilesFailed && interactive && <div className="float map-fallback-note">{'Street map could not load. Showing state outlines only.'}</div>}
    </>
  );
}
