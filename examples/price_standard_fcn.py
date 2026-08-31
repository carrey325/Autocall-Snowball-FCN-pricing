"""Price a standard FCN through the clean-room PDE engine."""

from structured_products import PDEConfig, MarketData, make_standard_fcn, price


product = make_standard_fcn(maturity_days=126, payment_days=(63, 126))
market = MarketData(
    spots=(100.0,),
    rate=0.03,
    dividend_yields=(0.0,),
    volatilities=(0.2,),
)
result = price(product, market, "pde", PDEConfig(spot_grid_points=201))
print(result.to_dict())
