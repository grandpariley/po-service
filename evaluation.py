import asyncio
import base64
import io
from itertools import cycle, combinations

import matplotlib.pyplot as plt

import db
from fetch_image import insert_image
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
        Log.log(
            "graph_solution_bigraph objective 1: " + str(objective_index1) + " objective 2: " + str(objective_index2))
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


async def graph_generations_arch1(name, generations):
    markers = cycle(MARKERS)
    colours = cycle(COLOURS)
    try:
        generations[0]['solutions'][0]['objectives']
    except IndexError:
        Log.log("WARNING: INDEX ERROR FOR [" + str(name) + "]")
        return
    except KeyError:
        Log.log("WARNING: KEY ERROR FOR [" + str(name) + "]")
        return

    for objective_index in range(len(generations[0]['solutions'][0]['objectives'])):
        plt.scatter(
            x=range(len(generations)),
            y=[generation['solutions'][0]['objectives'][0] for generation in generations],
            color=next(colours),
            marker=next(markers)
        )
    filename = name + '/generations.png'
    await save_image(filename)


async def get_generations(name, run):
    generations = []
    for generation in range(Constants.NUM_GENERATIONS):
        generation_data = await db.get_generation(name + "-" + str(run), generation)
        generations.append(generation_data)
    return generations


def get_table_vs_benchmark_one_solution(solution, benchmark):
    return {
        'return': {'solution': solution['objectives'][INDEX_TO_LABEL.index('return')],
                   'benchmark': benchmark['return']},
        'var': {'solution': solution['objectives'][INDEX_TO_LABEL.index('var')], 'benchmark': benchmark['var']},
        'cvar': {'solution': solution['objectives'][INDEX_TO_LABEL.index('cvar')], 'benchmark': benchmark['cvar']},
        'environment': {'solution': solution['objectives'][INDEX_TO_LABEL.index('environment')], 'benchmark': 'N/A'},
        'social': {'solution': solution['objectives'][INDEX_TO_LABEL.index('social')], 'benchmark': 'N/A'},
        'governance': {'solution': solution['objectives'][INDEX_TO_LABEL.index('governance')], 'benchmark': 'N/A'}
    }


def get_solution_for_investor(investor, solutions):
    weights = investor['weights']
    return match_portfolio(weights, solutions)


async def table_vs_benchmark_one_solution(investor, run, solutions, benchmark):
    Log.log("table_vs_benchmark_one_solution " + str(investor) + " " + str(run))
    solution = get_solution_for_investor(investor, solutions)
    await db.save_table_vs_benchmark('arch2-' + str(run), get_table_vs_benchmark_one_solution(solution, benchmark))


async def main(arch1_names):
    benchmark = await fetch('^GSPTSE')
    for run in range(Constants.NUM_RUNS * 2):
        for name in arch1_names:
            generations = await get_generations(name, run)
            await graph_generations_arch1(name + "-" + str(run), generations)
        arch2_solutions = await db.get_arch2_portfolios(run=run)
        for investor in Constants.INVESTORS:
            await table_vs_benchmark_one_solution(investor, run, arch2_solutions, benchmark)
        await graph_solution_bigraph_arch2(run, arch2_solutions)


if __name__ == '__main__':
    asyncio.run(main(['Alice', 'Sam', 'Jars']))
    Log.log("done evaluation~!")
