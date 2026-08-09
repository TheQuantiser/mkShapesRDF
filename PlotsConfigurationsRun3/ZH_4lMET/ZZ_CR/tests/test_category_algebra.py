import re


def _evaluate(expression, values):
    python_expr = expression.replace("&&", " and ").replace("||", " or ")
    python_expr = re.sub(r"!(?!=)", " not ", python_expr)
    return bool(eval(python_expr, {"__builtins__": {}}, dict(values)))


def _split(metadata, category_id, values):
    return _evaluate(metadata[category_id]["split_expression"], values)


def _values(z_flavor, x_flavor=None, stream=None):
    values = {
        "Z0_isEE": z_flavor == "EE",
        "Z0_isMM": z_flavor == "MM",
        "X_isEE": x_flavor == "EE",
        "X_isMM": x_flavor == "MM",
        "X_isSF": x_flavor in ("EE", "MM"),
        "X_isDF": x_flavor == "DF",
        "streamPriority_MuonEG": stream == "MUONEG",
        "streamPriority_Muon": stream == "MUON",
        "streamPriority_EGamma": stream == "EGAMMA",
    }
    return values


def test_dy_partition_and_intersection_algebra(load_state):
    metadata = load_state(category="standard")["CATEGORY_METADATA"]
    for z_flavor in ("EE", "MM"):
        for stream in ("MUONEG", "MUON", "EGAMMA"):
            values = _values(z_flavor, stream=stream)
            flavor_bits = [_split(metadata, f"DY_Z{flavor}", values) for flavor in ("EE", "MM")]
            stream_bits = [
                _split(metadata, f"DY_STREAM_{name}", values)
                for name in ("MUONEG", "MUON", "EGAMMA")
            ]
            assert sum(flavor_bits) == 1
            assert sum(stream_bits) == 1
            leaf_bits = []
            for stream_name in ("MUONEG", "MUON", "EGAMMA"):
                for flavor in ("EE", "MM"):
                    leaf = _split(metadata, f"DY_STREAM_{stream_name}_Z{flavor}", values)
                    assert leaf == (
                        _split(metadata, f"DY_STREAM_{stream_name}", values)
                        and _split(metadata, f"DY_Z{flavor}", values)
                    )
                    leaf_bits.append(leaf)
            assert sum(leaf_bits) == 1


def test_zzcr_partition_and_curated_intersections(load_state):
    metadata = load_state(category="standard")["CATEGORY_METADATA"]
    leaves = ("4E", "4MU", "2E2MU")
    curated = {
        "STREAM_EGAMMA_4E": ("STREAM_EGAMMA", "4E"),
        "STREAM_MUON_4MU": ("STREAM_MUON", "4MU"),
        "STREAM_MUONEG_2E2MU": ("STREAM_MUONEG", "2E2MU"),
        "STREAM_MUON_2E2MU": ("STREAM_MUON", "2E2MU"),
        "STREAM_EGAMMA_2E2MU": ("STREAM_EGAMMA", "2E2MU"),
    }
    for z_flavor in ("EE", "MM"):
        for x_flavor in ("EE", "MM"):
            for stream in ("MUONEG", "MUON", "EGAMMA"):
                values = _values(z_flavor, x_flavor, stream)
                assert sum(_split(metadata, f"ZZCR_{leaf}", values) for leaf in leaves) == 1
                for leaf, (stream_leaf, topology_leaf) in curated.items():
                    assert _split(metadata, f"ZZCR_{leaf}", values) == (
                        _split(metadata, f"ZZCR_{stream_leaf}", values)
                        and _split(metadata, f"ZZCR_{topology_leaf}", values)
                    )
    assert not any("XDF" in name for name in metadata if name.startswith("ZZCR_"))


def test_sr_topology_partition_and_x_flavor_algebra(load_state):
    metadata = load_state(category="standard")["CATEGORY_METADATA"]
    topology = ("4E", "4MU", "2E2MU", "3E1MU", "1E3MU")
    for z_flavor in ("EE", "MM"):
        for x_flavor in ("EE", "MM", "DF"):
            values = _values(z_flavor, x_flavor)
            bits = {leaf: _split(metadata, f"SR_{leaf}", values) for leaf in topology}
            assert sum(bits.values()) == 1
            assert _split(metadata, "SR_XSF", values) == (
                bits["4E"] or bits["4MU"] or bits["2E2MU"]
            )
            assert _split(metadata, "SR_XDF", values) == (
                bits["3E1MU"] or bits["1E3MU"]
            )
