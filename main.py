import asyncio
import functools
import os
import flask

from dotenv import load_dotenv
from flask import jsonify, request
from flask_cors import CORS

import db
import po.main
from po.match import match_portfolio
from po.pkg.log import Log
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights, \
    default_portfolio_optimization_problem_arch_2
from pomatch.pkg.response import Response, get_responses
from pomatch.pkg.weights import get_weights

load_dotenv()
BATCH_TASK_ID = 'batch'
tasks = {}
loop = asyncio.new_event_loop()
app = flask.Flask(__name__)
cors = CORS(app, resource={
    r"/*": {
        "origins": os.environ["FRONTEND_ORIGINS"].split(',')
    }
})


def task_done_callback(task_id, _):
    tasks.pop(task_id, None)


async def arch2():
    Log.log("arch 2 let's go!")
    await db.clear_arch2_portfolio()
    solutions = await po.main.main({
        'arch2': default_portfolio_optimization_problem_arch_2(),
    })
    await db.insert_arch2_portfolios(solutions['arch2'])


async def get_matched_portfolio(portfolio_id):
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await db.get_arch2_portfolios()
    return match_portfolio(weights, solutions)


async def portfolio_optimization(portfolio_id):
    Log.log("arch 1 let's go! " + portfolio_id)
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    })
    for name in solutions.keys():
        await db.insert_portfolio(portfolio_id, solutions[name])


async def get_portfolio_weights(portfolio_id):
    all_responses = await db.get_surveys()
    all_weights = get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    return weights


async def is_ready(task_id):
    return (task_id == BATCH_TASK_ID and await db.arch2_portfolios_exist()) or \
        (task_id == BATCH_TASK_ID and await db.portfolio_exists(task_id))


@app.route("/api/v1/batch", methods=["POST"])
def batch():
    Log.log("batch")
    tasks[BATCH_TASK_ID] = loop.create_task(arch2(), name=BATCH_TASK_ID)
    tasks[BATCH_TASK_ID].add_done_callback(functools.partial(task_done_callback, BATCH_TASK_ID))
    return jsonify({'status': 'PENDING'})


@app.route("/api/v1/batch/status")
def batch_status():
    return status(BATCH_TASK_ID)


@app.route("/api/v1/portfolio/<string:portfolio_id>/status")
def status(portfolio_id):
    Log.log("status: " + portfolio_id)
    if portfolio_id not in tasks.keys():
        return flask.Response(
            "task not found",
            status=404
        )
    if not tasks[portfolio_id].done():
        return jsonify({'status': 'PENDING'})
    if loop.run_until_complete(is_ready(portfolio_id)):
        return jsonify({'status': 'READY'})
    if tasks[portfolio_id].cancelled():
        return flask.Response(
            "task cancelled",
            status=500
        )
    return flask.Response(
        str(tasks[portfolio_id].exception()),
        status=500
    )


@app.route("/api/v1/survey", methods=["POST"])
def survey():
    Log.log("survey: " + request.json)
    portfolio_id = loop.run_until_complete(
        db.insert_survey(Response.model_construct(None, values=flask.json.loads(request.data))))
    tasks[portfolio_id] = loop.create_task(portfolio_optimization(portfolio_id), name=portfolio_id)
    tasks[portfolio_id].add_done_callback(functools.partial(task_done_callback, portfolio_id))
    return jsonify({'portfolio_id': portfolio_id})


@app.route("/api/v1/portfolio/<string:portfolio_id>")
def portfolio(portfolio_id):
    Log.log("survey status: " + portfolio_id)
    matched_portfolio = loop.run_until_complete(get_matched_portfolio(portfolio_id))
    custom_portfolios = loop.run_until_complete(db.get_portfolio(portfolio_id))
    matched_portfolio.pop('_id')
    return jsonify(custom_portfolios['portfolio'] + [matched_portfolio])


if __name__ == '__main__':
    app.run(port=2736, debug=True)
