"""Price a classic Snowball through the public API."""

from structured_products import MCConfig, MarketData, make_classic_snowball, price


product = make_classic_snowball(maturity_days=126)
market = MarketData(
    spots=(100.0,),
    rate=0.03,
    dividend_yields=(0.0,),
    volatilities=(0.2,),
)
result = price(product, market, "mc", MCConfig(n_paths=4_000, seed=7))
print(result.to_dict())
