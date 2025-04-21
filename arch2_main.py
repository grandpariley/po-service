import asyncio

import db
from po.main import main
from po.pkg.problem.builder import default_portfolio_optimization_problem_arch_2


async def arch2():
    await db.clear_arch2_portfolio()
    solutions = await main({
        'arch2': default_portfolio_optimization_problem_arch_2(),
    })
    await db.insert_arch2_portfolios(solutions['arch2'])


if __name__ == '__main__':
    asyncio.run(arch2())
