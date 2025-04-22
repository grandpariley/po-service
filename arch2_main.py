import asyncio

import db
from po.main import main
from po.pkg.problem.builder import default_portfolio_optimization_problem_arch_2, \
    default_portfolio_optimization_problem_arch_1


async def arch2():
    solutions = await main({
        'arch2': default_portfolio_optimization_problem_arch_2(),
        'Alice': default_portfolio_optimization_problem_arch_1('Alice'),
        'Sam': default_portfolio_optimization_problem_arch_1('Sam'),
        'Jars': default_portfolio_optimization_problem_arch_1('Jars')
    })
    await db.clear_arch2_portfolio()
    await db.insert_arch2_portfolios(solutions['arch2'])
    await db.insert_portfolio('Alice', solutions['Alice'])
    await db.insert_portfolio('Sam', solutions['Sam'])
    await db.insert_portfolio('Jars', solutions['Jars'])


if __name__ == '__main__':
    asyncio.run(arch2())
