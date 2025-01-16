import asyncio
import os

import flask
from dotenv import load_dotenv
from flask import jsonify, request
from flask_cors import CORS
import logging

import db
from pomatch.pkg.response import Response

load_dotenv()
HEALTH_CHECK_ID = 'health_check'
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
app.logger.info("connecting to rabbit....")
import queue_broker

app.logger.info("connected to rabbit!")
app.logger.info("creating queue....")
queue_broker.create()
app.logger.info("created queue!")


@app.route("/api/v1/health", methods=["GET"])
def health():
    app.logger.info("HEALTH CHECK")
    queue_broker.publish(HEALTH_CHECK_ID)
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
    app.logger.info("survey: " + str(request.json))
    portfolio_id = asyncio.run(db.insert_survey(Response.model_construct(None, values=flask.json.loads(request.data))))
    queue_broker.publish(portfolio_id)
    return jsonify({'portfolio_id': portfolio_id})


@app.route("/api/v1/portfolio/<string:portfolio_id>")
def portfolio(portfolio_id):
    app.logger.info("survey status: " + portfolio_id)
    custom_portfolios = asyncio.run(db.get_portfolio(portfolio_id))
    return jsonify(custom_portfolios['portfolio'])
