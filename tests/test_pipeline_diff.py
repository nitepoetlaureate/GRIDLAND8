from backend.pipeline.diff import AircraftDiffer


def ac(icao, lat=0.0, lon=0.0, alt=1000.0, track=90.0, vel=200.0, cs=None, gnd=False):
    return {"icao24": icao, "lat": lat, "lon": lon, "alt_m": alt,
            "track_deg": track, "velocity_ms": vel, "callsign": cs,
            "on_ground": gnd}


def test_first_frame_is_snapshot():
    d = AircraftDiffer()
    f = d.next_frame([ac("a"), ac("b")], "t0")
    assert f["kind"] == "snapshot"
    assert {x["icao24"] for x in f["items"]} == {"a", "b"}


def test_unchanged_yields_empty_diff():
    d = AircraftDiffer()
    d.next_frame([ac("a", lat=1.0)], "t0")
    f = d.next_frame([ac("a", lat=1.0)], "t1")
    assert f["kind"] == "diff"
    assert f["added"] == [] and f["updated"] == [] and f["removed"] == []


def test_position_change_yields_update_only():
    d = AircraftDiffer()
    d.next_frame([ac("a", lat=1.0)], "t0")
    f = d.next_frame([ac("a", lat=2.0)], "t1")
    assert f["kind"] == "diff"
    assert len(f["updated"]) == 1
    assert f["updated"][0]["lat"] == 2.0
    assert f["added"] == [] and f["removed"] == []


def test_new_aircraft_added():
    d = AircraftDiffer()
    d.next_frame([ac("a")], "t0")
    f = d.next_frame([ac("a"), ac("b")], "t1")
    assert [x["icao24"] for x in f["added"]] == ["b"]


def test_disappeared_aircraft_removed():
    d = AircraftDiffer()
    d.next_frame([ac("a"), ac("b")], "t0")
    f = d.next_frame([ac("a")], "t1")
    assert f["removed"] == ["b"]
    assert f["added"] == [] and f["updated"] == []


def test_callsign_change_counts_as_update():
    d = AircraftDiffer()
    d.next_frame([ac("a", cs=None)], "t0")
    f = d.next_frame([ac("a", cs="UAL1")], "t1")
    assert len(f["updated"]) == 1


def test_reset_clears_state():
    d = AircraftDiffer()
    d.next_frame([ac("a")], "t0")
    d.reset()
    f = d.next_frame([ac("a")], "t1")
    assert f["kind"] == "snapshot"
