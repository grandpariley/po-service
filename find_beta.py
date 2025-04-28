import asyncio

import db
from po.match import match_portfolio
from po.pkg.consts import Constants
from po.pkg.data import fetch

async def find_beta(solution):
    objective_value = 0
    for key, value in solution['variables'].items():
        d = await fetch(key)
        if d['beta'] is None:
            continue
        how_much_of_budget = d['price'] * value / Constants.BUDGET
        objective_value += d['beta'] * how_much_of_budget
    return objective_value


async def main():
    for run in range(1):
        arch2_portfolios = await db.get_arch2_portfolios(run)
        for investor in Constants.INVESTORS:
            arch2_portfolio = match_portfolio(investor['weights'], arch2_portfolios)
            arch2_b = await find_beta(arch2_portfolio)
            await db.insert_beta('arch2-' + investor['person'] + '-' + str(run), arch2_b)
            arch1_portfolio = (await db.get_portfolio(investor['person'] + '-' + str(run)))['portfolio'][0]
            arch1_b = await find_beta(arch1_portfolio)
            await db.insert_beta(investor['person'] + '-' + str(run), arch1_b)



if __name__ == "__main__":
    asyncio.run(main())