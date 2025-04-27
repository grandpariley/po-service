import asyncio

import db
from po.main import main
from evaluation import main as evaluate
from po.pkg.consts import Constants
from po.pkg.problem.builder import default_portfolio_optimization_problem_arch_2, \
    default_portfolio_optimization_problem_arch_1


async def arch2():
    for run in range(Constants.NUM_RUNS * 2):
        solutions = await main({
            'arch2-' + str(run): default_portfolio_optimization_problem_arch_2(),
            'Alice-' + str(run): default_portfolio_optimization_problem_arch_1('Alice'),
            'Sam-' + str(run): default_portfolio_optimization_problem_arch_1('Sam'),
            'Jars-' + str(run): default_portfolio_optimization_problem_arch_1('Jars')
        }, run)
        await db.clear_arch2_portfolio(run)
        await db.insert_arch2_portfolios(run, solutions['arch2-' + str(run)])
        for name in solutions.keys():
            if 'arch2' in name:
                continue
            await db.insert_portfolio(name, solutions[name])



if __name__ == '__main__':
    # asyncio.run(arch2())
    asyncio.run(evaluate(['Alice', 'Sam', 'Jars']))
