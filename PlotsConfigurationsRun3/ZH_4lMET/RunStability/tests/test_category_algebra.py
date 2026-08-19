import itertools


def _eval(expression, values):
    result = expression
    for name in sorted(values, key=len, reverse=True):
        result = result.replace(name, str(bool(values[name])))
    result = result.replace("&&", " and ").replace("||", " or ")
    return bool(eval(result, {"__builtins__": {}}, {}))


def test_dy_flavor_stream_and_intersection_algebra(load_state):
    metadata = load_state()["CATEGORY_METADATA"]
    flavors = ("ZEE", "ZMM")
    streams = ("MUONEG", "MUON", "EGAMMA")
    stream_columns = {
        "MUONEG": "streamPriority_MuonEG",
        "MUON": "streamPriority_Muon",
        "EGAMMA": "streamPriority_EGamma",
    }

    for zee, zmm in ((True, False), (False, True)):
        for active_stream in streams:
            values = {
                "Z0_isEE": zee,
                "Z0_isMM": zmm,
                **{
                    column: name == active_stream
                    for name, column in stream_columns.items()
                },
            }
            assert (
                sum(
                    _eval(metadata[f"DY_{flavor}"]["split_expression"], values)
                    for flavor in flavors
                )
                == 1
            )
            assert (
                sum(
                    _eval(metadata[f"DY_STREAM_{stream}"]["split_expression"], values)
                    for stream in streams
                )
                == 1
            )
            assert (
                sum(
                    _eval(
                        metadata[f"DY_STREAM_{stream}_{flavor}"]["split_expression"],
                        values,
                    )
                    for stream, flavor in itertools.product(streams, flavors)
                )
                == 1
            )
