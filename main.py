import asyncio
import os
import flask
import logging

from dotenv import load_dotenv
from flask import jsonify, request
from flask_cors import CORS

import db
import po.main
from po.match import match_portfolio
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights, \
    default_portfolio_optimization_problem_arch_2
from pomatch.pkg.response import Response, get_responses
from pomatch.pkg.weights import get_weights

load_dotenv()
BATCH_TASK_ID = 'batch'
app = flask.Flask(__name__)
cors = CORS(app, resource={
    r"/*": {
        "origins": os.environ["FRONTEND_ORIGINS"].split(',')
    }
})
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


def listen(portfolio_id):
    if BATCH_TASK_ID == portfolio_id:
        asyncio.run(arch2())
    else:
        asyncio.run(portfolio_optimization(portfolio_id))

app.logger.info("connecting to rabbit....")
import queue_broker
app.logger.info("connected to rabbit!")
app.logger.info("registering....")
queue_broker.register_listener(listen)
app.logger.info("registered!")


async def arch2():
    app.logger.info("arch 2 let's go!")
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
    app.logger.info("arch 1 let's go! " + portfolio_id)
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


@app.route("/api/v1/health", methods=["GET"])
def health():
    app.logger.info("HEALTH CHECK")
    return jsonify({"status": "yup"})

@app.route("/api/v1/batch", methods=["POST"])
def batch():
    app.logger.info("batch")
    asyncio.run(db.insert_queue(BATCH_TASK_ID))
    queue_broker.publish(BATCH_TASK_ID)
    return batch_status()


@app.route("/api/v1/batch/status")
def batch_status():
    return status(BATCH_TASK_ID)


@app.route("/api/v1/portfolio/<string:portfolio_id>/status")
def status(portfolio_id):
    app.logger.info("status: " + portfolio_id)
    s = asyncio.run(db.get_queue(portfolio_id))
    if not s:
        return flask.Response(
            "task not found",
            status=404
        )
    return jsonify(s)


@app.route("/api/v1/survey", methods=["POST"])
def survey():
    app.logger.info("survey: " + request.json)
    portfolio_id = asyncio.run(db.insert_survey(Response.model_construct(None, values=flask.json.loads(request.data))))
    queue_broker.publish(portfolio_id)
    return jsonify({'portfolio_id': portfolio_id})


@app.route("/api/v1/portfolio/<string:portfolio_id>")
def portfolio(portfolio_id):
    app.logger.info("survey status: " + portfolio_id)
    matched_portfolio = asyncio.run(get_matched_portfolio(portfolio_id))
    custom_portfolios = asyncio.run(db.get_portfolio(portfolio_id))
    matched_portfolio.pop('_id')
    return jsonify(custom_portfolios['portfolio'] + [matched_portfolio])
