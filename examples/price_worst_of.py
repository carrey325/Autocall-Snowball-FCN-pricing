"""Price a two-asset worst-of Snowball."""

from structured_products import MCConfig, MarketData, make_worst_of_snowball, price


product = make_worst_of_snowball(
    reference_spots=(100.0, 100.0), maturity_days=126
)
market = MarketData(
    spots=(100.0, 100.0),
    rate=0.03,
    dividend_yields=(0.0, 0.0),
    volatilities=(0.2, 0.25),
    correlation=((1.0, 0.4), (0.4, 1.0)),
)
result = price(product, market, "mc", MCConfig(n_paths=4_000, seed=7))
print(result.to_dict())
