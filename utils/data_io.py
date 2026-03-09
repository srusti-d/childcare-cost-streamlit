import json
import copy
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape



def _fix_fips_digits(val) -> str:
    """Zero-pad a FIPS code to exactly 5 digits."""
    val = str(val)
    if len(val) == 5:
        return val
    if len(val) == 4:
        return "0" + val
    return "Incorrect Digits"


def _iter_coords(coords):
    """Get every (x, y) pair from nested GeoJSON coordinates."""
    if not coords:
        return
    if isinstance(coords[0], (int, float)) and len(coords) == 2:
        yield coords
    else:
        for c in coords:
            yield from _iter_coords(c)


def _transform_coords(coords, fx):
    if not coords:
        return coords
    if isinstance(coords[0], (int, float)) and len(coords) == 2:
        x, y = coords
        x2, y2 = fx(x, y)
        return [x2, y2]
    return [_transform_coords(c, fx) for c in coords]


def normalize_features_to_unit_box(features: list, pad: float = 0.03) -> list:
    """
    Normalise all geometries in *features* so they fill a [0,1] by [0,1] box
    for state-specific maps.
    """
    xs, ys = [], []
    for feat in features:
        for x, y in _iter_coords(feat.get("geometry", {}).get("coordinates", [])):
            xs.append(x)
            ys.append(y)

    if not xs or not ys:
        return features

    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    s = max((xmax - xmin) or 1.0, (ymax - ymin) or 1.0)

    def fx(x, y):
        xn = pad + ((x - xmin) / s) * (1 - 2 * pad)
        yn = pad + ((y - ymin) / s) * (1 - 2 * pad)
        return xn, yn

    out = []
    for feat in features:
        feat2 = copy.deepcopy(feat)
        geom = feat2.get("geometry", {})
        geom["coordinates"] = _transform_coords(geom.get("coordinates", []), fx)
        feat2["geometry"] = geom
        out.append(feat2)
    return out



def load_raw_data(
    childcare_path: str = "./data/childcare_costs.csv",
    counties_path: str = "./data/counties.csv",
    rucc_path: str = "./data/Ruralurbancontinuumcodes2023.csv",
    geojson_path: str = "./data/geojson-counties-fips.json",
) -> dict:
    """
    Load every raw data source and return them in a dict keyed by name.
    """
    child_data = pd.read_csv(childcare_path)
    county_data = pd.read_csv(counties_path)
    rucc = pd.read_csv(rucc_path, encoding="latin1")

    with open(geojson_path, "r") as f:
        geo_counties_raw = json.load(f)

    # Return 5-digit fips5 property on every GeoJSON feature
    for feature in geo_counties_raw["features"]:
        p = feature["properties"]
        p["fips5"] = str(p["STATE"]).zfill(2) + str(p["COUNTY"]).zfill(3)

    feats = geo_counties_raw["features"]
    US_map_df = pd.DataFrame(
        {
            "features": feats,
            "geometry": [f["geometry"] for f in feats],
            "county_name": [f["properties"]["NAME"] for f in feats],
            "county_fips_code": [f["properties"]["fips5"] for f in feats],
            "county_id": [f["properties"]["COUNTY"] for f in feats],
            "state_id": [f["properties"]["STATE"] for f in feats],
        }
    )

    return {
        "child_data": child_data,
        "county_data": county_data,
        "rucc": rucc,
        "US_map_df": US_map_df,
        "geo_counties_raw": geo_counties_raw,
    }


def preprocess_base(raw: dict) -> dict:
    """
    Normalise FIPS codes, get state_id, merge child + county, attach state_name to map.
    """
    child_data = raw["child_data"].copy()
    county_data = raw["county_data"].copy()
    US_map_df = raw["US_map_df"].copy()

    child_data["county_fips_code"] = child_data["county_fips_code"].apply(_fix_fips_digits)
    county_data["county_fips_code"] = county_data["county_fips_code"].apply(_fix_fips_digits)

    child_data["state_id"] = child_data["county_fips_code"].str[:2]
    county_data["state_id"] = county_data["county_fips_code"].str[:2]

    data_merged = child_data.merge(
        county_data, on="county_fips_code", how="left", suffixes=("", "_county")
    )

    if "state_id_county" in data_merged.columns:
        data_merged["state_id"] = data_merged["state_id"].fillna(
            data_merged.pop("state_id_county")
        )

    state_name_map = (
        data_merged[["state_id", "state_name"]]
        .drop_duplicates()
        .dropna(subset=["state_name"])
    )
    US_map_df = US_map_df.merge(state_name_map, on="state_id", how="left")

    return {
        "child_data": child_data,
        "county_data": county_data,
        "data_merged": data_merged,
        "US_map_df": US_map_df,
    }


def build_state_metrics(data_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Returns dataframe with state_id, study_year, mcsa_mean, pr_f_mean, flfpr_20to64_mean, state_name.
    """
    state_metrics = (
        data_merged.groupby(["state_id", "study_year"])
        .agg(
            mcsa_mean=("mcsa", "mean"),
            pr_f_mean=("pr_f", "mean"),
            flfpr_20to64_mean=("flfpr_20to64", "mean"),
        )
        .reset_index()
    )
    state_metrics["state_id"] = state_metrics["state_id"].astype(str).str.zfill(2)

    state_name_lookup = (
        data_merged[["state_id", "state_name"]]
        .drop_duplicates()
        .dropna(subset=["state_name"])
    )
    state_metrics = state_metrics.merge(state_name_lookup, on="state_id", how="left")
    return state_metrics


def build_geo_features(US_map_df: pd.DataFrame, state_metrics: pd.DataFrame) -> list:
    """
    Dissolve county geometries to state level, merge with state_metrics, and
    return a flat list of GeoJSON features with mcsa_mean, pr_f_mean, flfpr_20to64_mean.
    """
    gdf = gpd.GeoDataFrame(
        US_map_df[["county_name", "county_fips_code", "county_id", "state_id"]],
        geometry=US_map_df["geometry"].apply(shape),
        crs="EPSG:4326",
    )

    state_gdf = gdf.dissolve(by="state_id").reset_index()
    state_gdf["state_id"] = state_gdf["state_id"].astype(str).str.zfill(2)
    state_gdf_clean = state_gdf[["state_id", "geometry"]].copy()

    state_name_lookup = (
        state_metrics[["state_id", "state_name"]]
        .drop_duplicates()
        .dropna(subset=["state_name"])
    )
    state_gdf_clean = state_gdf_clean.merge(state_name_lookup, on="state_id", how="left")

    metric_cols = ["state_id", "state_name", "mcsa_mean", "pr_f_mean", "flfpr_20to64_mean"]
    all_features = []
    for year, group in state_metrics.groupby("study_year"):
        merged = state_gdf_clean.merge(
            group[metric_cols], on="state_id", how="left", suffixes=("", "_dup")
        )
        merged = merged.loc[:, ~merged.columns.str.endswith("_dup")]
        geojson_dict = json.loads(merged.to_json())
        for feature in geojson_dict["features"]:
            feature["properties"]["study_year"] = int(year)
            all_features.append(feature)

    return all_features


def build_rucc_panel(data_merged: pd.DataFrame, rucc: pd.DataFrame) -> pd.DataFrame:
    """
    Attach RUCC 2023 codes, derive binary urbanicity_rucc label, drop unmatched.
    """
    rucc_2023 = (
        rucc.loc[rucc["Attribute"] == "RUCC_2023", ["FIPS", "Value"]]
        .copy()
        .assign(
            county_fips_code=lambda d: d["FIPS"].astype(str).str.zfill(5),
            RUCC_2023=lambda d: pd.to_numeric(d["Value"], errors="coerce"),
        )[["county_fips_code", "RUCC_2023"]]
        .drop_duplicates()
    )

    data_with_rucc = data_merged.merge(rucc_2023, on="county_fips_code", how="left")
    data_with_rucc["urbanicity_rucc"] = data_with_rucc["RUCC_2023"].apply(
        lambda x: "Urban" if pd.notna(x) and x <= 3 else ("Rural" if pd.notna(x) else None)
    )
    return data_with_rucc.dropna(subset=["urbanicity_rucc"]).copy()


def build_sample_county_avg(
    df_rucc_valid: pd.DataFrame,
    sample_states: list | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    County-level and state-level averages of mcsa, pr_p, flfpr_20to64
    for the sample states (averaged across all study years).
    """
    if sample_states is None:
        sample_states = [
            "North Dakota",
            "Kansas",
            "Oklahoma",
            "Vermont",  # rural
            "Massachusetts",
            "California",
            "Arizona",
            "Delaware",  # urban
        ]

    COST, WLF, POV = "mcsa", "flfpr_20to64", "pr_p"
    df_sample = df_rucc_valid[df_rucc_valid["state_name"].isin(sample_states)].copy()

    county_avg = (
        df_sample.groupby(
            ["county_fips_code", "state_name", "state_id", "county_name", "urbanicity_rucc"],
            dropna=False,
        )[[COST, WLF, POV]]
        .mean()
        .reset_index()
    )
    county_avg["county_fips_code"] = county_avg["county_fips_code"].astype(str).str.zfill(5)

    state_avg = (
        county_avg.groupby(["state_name"], dropna=False)[[COST, WLF, POV]]
        .mean()
        .reset_index()
    )

    return county_avg, state_avg


def build_geo_merged(
    df_rucc_valid: pd.DataFrame,
    geo_counties_raw: dict,
) -> gpd.GeoDataFrame:
    """
    Build a county-level GeoDataFrame for per-year child data metrics and urbanicity labels.
    """
    rural_states = ["North Dakota", "Kansas", "Oklahoma", "Vermont"]
    urban_states = ["Massachusetts", "California", "Arizona", "Delaware"]

    feats = geo_counties_raw["features"]
    gdf_counties = gpd.GeoDataFrame(
        {
            "county_fips_code": [f["properties"]["fips5"] for f in feats],
            "county_name": [f["properties"]["NAME"] for f in feats],
        },
        geometry=[shape(f["geometry"]) for f in feats],
        crs="EPSG:4326",
    )
    gdf_counties["county_fips_code"] = gdf_counties["county_fips_code"].astype(str).str.zfill(5)

    def assign_group(state):
        if state in rural_states:
            return "Rural"
        if state in urban_states:
            return "Urban"
        return None

    keep_cols = [
        "county_fips_code",
        "state_name",
        "state_id",
        "study_year",
        "mcsa",
        "pr_p",
        "flfpr_20to64",
        "urbanicity_rucc",
    ]
    child_small = df_rucc_valid[keep_cols].copy()
    child_small["county_fips_code"] = child_small["county_fips_code"].astype(str).str.zfill(5)
    child_small["state_group"] = child_small["state_name"].apply(assign_group)
    child_small = child_small[child_small["state_group"].notna()]

    return gdf_counties.merge(child_small, on="county_fips_code", how="inner")


def build_cost_trend(data_merged: pd.DataFrame) -> pd.DataFrame:
    """
    National average childcare cost (mcsa) per study year across all counties.
    """
    return data_merged.groupby("study_year")["mcsa"].mean().reset_index()


def load_and_preprocess_all(
    childcare_path: str = "./data/childcare_costs.csv",
    counties_path: str = "./data/counties.csv",
    rucc_path: str = "./data/Ruralurbancontinuumcodes2023.csv",
    geojson_path: str = "./data/geojson-counties-fips.json",
    sample_states: list | None = None,
) -> dict:
    """
    Run the full preprocessing and return every dataframe version needed by charts.py.
    """
    if sample_states is None:
        sample_states = [
            "North Dakota",
            "Kansas",
            "Oklahoma",
            "Vermont",  # rural
            "Massachusetts",
            "California",
            "Arizona",
            "Delaware",  # urban
        ]

    raw = load_raw_data(childcare_path, counties_path, rucc_path, geojson_path)
    base = preprocess_base(raw)
    dm = base["data_merged"]

    state_metrics = build_state_metrics(dm)
    geo_features = build_geo_features(base["US_map_df"], state_metrics)
    df_rucc_valid = build_rucc_panel(dm, raw["rucc"])
    county_avg, state_avg = build_sample_county_avg(df_rucc_valid, sample_states)
    geo_merged = build_geo_merged(df_rucc_valid, raw["geo_counties_raw"])
    geo_merged_json = json.loads(geo_merged.to_json())
    cost_trend = build_cost_trend(dm)

    return {
        "child_data": base["child_data"],
        "county_data": base["county_data"],
        "data_merged": dm,
        "US_map_df": base["US_map_df"],
        "state_metrics": state_metrics,
        "geo_features": geo_features,
        "df_rucc_valid": df_rucc_valid,
        "county_avg": county_avg,
        "state_avg": state_avg,
        "geo_merged": geo_merged,
        "cost_trend": cost_trend,
        "geo_counties_raw": raw["geo_counties_raw"],
        "geo_merged_json": geo_merged_json,
        "sample_states": sample_states,
    }