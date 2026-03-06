from pathlib import Path
import json
import shapefile  # pyshp


def main():
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    SHP_PATH = PROJECT_ROOT / "data" / "geo" / "Admin2.shp"
    OUT_PATH = PROJECT_ROOT / "app" / "assets" / "india_states.geojson"

    print("📌 PROJECT_ROOT:", PROJECT_ROOT)
    print("📌 SHP_PATH:", SHP_PATH)
    print("📌 OUT_PATH:", OUT_PATH)

    if not SHP_PATH.exists():
        raise FileNotFoundError(f"Shapefile not found: {SHP_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("✅ Reading shapefile (no geopandas)...")
    r = shapefile.Reader(str(SHP_PATH), encoding="utf-8", errors="ignore")

    fields = [f[0] for f in r.fields[1:]]  # skip deletion flag
    if "ST_NM" not in fields:
        raise KeyError(f"'ST_NM' not found in shapefile fields: {fields}")

    st_index = fields.index("ST_NM")

    # Collect all polygons grouped by state
    state_geoms = {}

    for sr in r.shapeRecords():
        state = sr.record[st_index]
        geom = sr.shape.__geo_interface__

        if geom["type"] == "Polygon":
            coords = geom["coordinates"]
            state_geoms.setdefault(state, []).append(coords)

        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                state_geoms.setdefault(state, []).append(poly)

    # Build state-level GeoJSON (MultiPolygon per state)
    features = []
    for state, polys in state_geoms.items():
        feat = {
            "type": "Feature",
            "properties": {"state_name": state},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": polys
            }
        }
        features.append(feat)

    geojson = {"type": "FeatureCollection", "features": features}

    OUT_PATH.write_text(json.dumps(geojson), encoding="utf-8")

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"✅ DONE! GeoJSON saved: {OUT_PATH} ({size_kb:.2f} KB)")
    print(f"✅ States in GeoJSON: {len(features)}")


if __name__ == "__main__":
    main()
