import asyncio
import base64
import io
from itertools import cycle, combinations

import matplotlib.pyplot as plt

import db
from image.fetch_image import insert_image
from po.match import match_portfolio
from po.pkg.consts import Constants
from po.pkg.data import fetch
from po.pkg.log import Log

COLOURS = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'aquamarine', 'mediumseagreen', 'burlywood', 'coral']
MARKERS = ['.', 'o', 'v', '^', '<', '>', 's', 'x', 'd', '|', '_']
INDEX_TO_LABEL = ['cvar', 'var', 'return', 'environment', 'governance', 'social']
LABELS = {
    'arch2': 'Architecture 2',
    'arch1-sam': 'Sam',
    'arch1-jars': 'Jars',
    'arch1-alice': 'Alice'
}


async def save_image(filename):
    bytesio = io.BytesIO()
    plt.savefig(bytesio, format='png')
    plt.clf()
    bytesio.seek(0)
    await insert_image(filename, base64.b64encode(bytesio.read()))


async def graph_solution_bigraph_arch2(run, solutions):
    for (objective_index1, objective_index2) in combinations(range(len(INDEX_TO_LABEL)), 2):
        if objective_index1 == objective_index2:
            continue
        colours = cycle(COLOURS)
        colour = next(colours)
        for s in range(len(solutions)):
            plt.scatter(
                x=[solutions[s]['objectives'][objective_index2]],
                y=[solutions[s]['objectives'][objective_index1]],
                marker='$' + str(s) + '$',
                color=colour,
            )
        plt.xlabel(INDEX_TO_LABEL[objective_index2])
        plt.ylabel(INDEX_TO_LABEL[objective_index1])
        filename = 'arch2-' + str(run) + '/' + INDEX_TO_LABEL[objective_index1] + '-' + INDEX_TO_LABEL[
            objective_index2] + '.png'
        await save_image(filename)


async def graph_generations_arch2(run, investor, generations):
    markers = cycle(MARKERS)
    colours = cycle(COLOURS)

    for objective_index in range(len(INDEX_TO_LABEL)):
        y = []
        for generation in generations:
            best_solution = get_solution_for_investor(investor, generation['solutions'])
            y.append(best_solution['objectives'][objective_index])
        plt.scatter(
            x=range(len(generations)),
            y=y,
            color=next(colours),
            marker=next(markers)
        )
        plt.xlabel("generation")
        plt.ylabel(INDEX_TO_LABEL[objective_index])
        filename = 'arch2-' + str(run) + '/' + investor['person'] + '-' + INDEX_TO_LABEL[
            objective_index] + '-generations.png'
        await save_image(filename)


async def get_generations(name, run):
    generations = []
    for generation in range(Constants.NUM_GENERATIONS):
        generation_data = await db.get_generation(name + "-" + str(run), generation)
        if generation_data is None:
            Log.log("WARNING: GENERATION NOT FOUND: " + name + "-" + str(run) + " gen " + str(generation))
            continue
        generations.append(generation_data)
    return generations


def get_table_vs_benchmark_one_solution_arch2(solution, benchmark):
    return {
        'return': {'solution': solution['objectives'][INDEX_TO_LABEL.index('return')],
                   'benchmark': benchmark['return']},
        'var': {'solution': solution['objectives'][INDEX_TO_LABEL.index('var')], 'benchmark': benchmark['var']},
        'cvar': {'solution': solution['objectives'][INDEX_TO_LABEL.index('cvar')], 'benchmark': benchmark['cvar']},
        'environment': {'solution': solution['objectives'][INDEX_TO_LABEL.index('environment')], 'benchmark': 'N/A'},
        'social': {'solution': solution['objectives'][INDEX_TO_LABEL.index('social')], 'benchmark': 'N/A'},
        'governance': {'solution': solution['objectives'][INDEX_TO_LABEL.index('governance')], 'benchmark': 'N/A'}
    }


def get_table_vs_benchmark_one_solution_arch1(weights, solution, benchmark):
    ov = solution['objectives'][0]
    return {
        'return': {'solution': decompose(ov, weights['return']), 'benchmark': benchmark['return']},
        'var': {'solution': decompose(ov, weights['var']), 'benchmark': benchmark['var']},
        'cvar': {'solution': decompose(ov, weights['cvar']), 'benchmark': benchmark['cvar']},
        'environment': {'solution': decompose(ov, weights['environment']), 'benchmark': 'N/A'},
        'social': {'solution': decompose(ov, weights['social']), 'benchmark': 'N/A'},
        'governance': {'solution': decompose(ov, weights['governance']), 'benchmark': 'N/A'}
    }


def decompose(ov, weight):
    if weight == 0:
        return 0
    return ov / weight


def get_solution_for_investor(investor, solutions):
    weights = investor['weights']
    return match_portfolio(weights, solutions)


async def table_vs_benchmark_arch2(investor, run, solutions, benchmark):
    Log.log("table_vs_benchmark arch 2 - " + str(investor['person']) + "-" + str(run))
    solution = get_solution_for_investor(investor, solutions)
    if solution is None:
        Log.log("WARNING: NO SOLUTION FOUND FOR " + str(investor['person']))
        return
    await db.save_table_vs_benchmark('arch2-' + str(run),
                                     get_table_vs_benchmark_one_solution_arch2(solution, benchmark))


async def table_vs_benchmark_arch1(investor, run, solution, benchmark):
    Log.log("table_vs_benchmark arch 1 - " + str(investor['person']) + "-" + str(run))
    await db.save_table_vs_benchmark(investor['person'] + '-' + str(run),
                                     get_table_vs_benchmark_one_solution_arch1(investor['weights'], solution,
                                                                               benchmark))


async def evaluate():
    benchmark = await fetch('^GSPTSE')
    for run in range(Constants.NUM_RUNS):
        generations = await get_generations('arch2', run)
        arch2_solutions = await db.get_arch2_portfolios(run=run)
        await graph_solution_bigraph_arch2(run, arch2_solutions)
        for investor in Constants.INVESTORS:
            await graph_generations_arch2(run, investor, generations)
            await table_vs_benchmark_arch2(investor, run, arch2_solutions, benchmark)
            investor_arch1_solution = await db.get_portfolio(investor['person'] + "-" + str(run))
            await table_vs_benchmark_arch1(investor, run, investor_arch1_solution['portfolio'][0], benchmark)


if __name__ == '__main__':
    asyncio.run(evaluate())
    Log.log("done evaluation~!")


# TODO
# - add beta to table vs benchmark
# - figure out why benchmark numbers are fucked
# - scaled?