from stop_hunt_strategy.data.cmc_ohlcv import parse_ohlcv_payload


def test_parse_ohlcv_payload_normalizes_rows() -> None:
    payload = {
        "status": {"error_code": 0},
        "data": {
            "1": {
                "quotes": [
                    {
                        "time_open": "2024-01-01T00:00:00.000Z",
                        "quote": {
                            "USD": {
                                "open": 100.0,
                                "high": 110.0,
                                "low": 90.0,
                                "close": 105.0,
                                "volume": 12345.6,
                                "market_cap": 999.0,
                            }
                        },
                    },
                    {
                        "time_open": "2024-01-01T01:00:00.000Z",
                        "quote": {
                            "USD": {
                                "open": 105.0,
                                "high": 112.0,
                                "low": 101.0,
                                "close": 111.0,
                                "volume": 14000.0,
                                "market_cap": 1001.0,
                            }
                        },
                    },
                ]
            }
        },
    }

    df = parse_ohlcv_payload(payload=payload, symbol="BTC", interval="hourly")

    assert len(df) == 2
    assert list(df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "market_cap",
        "symbol",
        "pair",
        "interval",
        "source",
    ]
    assert df.iloc[0]["symbol"] == "BTC"
    assert df.iloc[0]["pair"] == "btcusdt.p"
    assert df.iloc[0]["interval"] == "hourly"
    assert str(df.iloc[0]["timestamp"].tz) == "UTC"
