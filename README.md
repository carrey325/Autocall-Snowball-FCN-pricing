# Structured Products Pricer

A lightweight pricing framework for Snowball, FCN, and autocallable structured products.

This project focuses on practical pricing and product comparison for a core set of structured products. It provides a unified product interface, Monte Carlo and PDE pricing. 


## Method&products support

| Product | Monte Carlo | PDE |
|---|---:|---:|
| Snowball | Yes | Yes |
| FCN | Yes | Yes |
| Classic autocall | Yes | Yes |
| Wide autocall | Yes | Yes |
| Dividend autocall | Yes | Yes |
| Butterfly autocall | Yes | Yes |
| Step-down autocall | Yes | No |

Step-down autocall is Monte Carlo only.

## Product overview

### Snowball
A structured product with knock-in and knock-out features, designed for range-bound market views with enhanced coupon potential.

### FCN
A fixed coupon note that offers coupon income under predefined barrier conditions.

### Classic autocall
A standard autocallable structure with fixed knock-in barrier, fixed knock-out barrier, and fixed coupon.

### Wide autocall
A more defensive version of the classic autocall, usually with a lower knock-in barrier, a wider payoff range, and a lower coupon.

### Dividend autocall
An autocall structure with two coupon outcomes: a higher coupon if the product knocks out early, and a lower maturity coupon if it survives without knock-in and knock-out.

### Butterfly autocall
An autocall structure with a time-varying coupon schedule, typically offering higher coupons for earlier redemption and lower coupons later.

### Step-down autocall
An autocall structure with a knock-out barrier that decreases over time, making redemption easier in later observation periods.

## Pricing framework

All autocall products are handled through a common event-driven framework based on:

- knock-in monitoring
- knock-out observation
- coupon schedule evaluation
- maturity payoff handling

Monte Carlo is the primary pricing method for the full autocall family. PDE is provided for the simpler structures where the payoff mapping is straightforward.