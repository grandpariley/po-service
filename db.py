import asyncio
import json
import os
from json import JSONDecoder

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv

from po.pkg.log import Log
from po.pkg.problem.problem import problem_encoder_fn

load_dotenv()
BATCH_TASK_ID = 'batch'

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
arch2_portfolio = client.po.get_collection('arch2_portfolio')
survey = client.po.get_collection('survey')
queue_status = client.po.get_collection('queue')
generation = client.po.get_collection('generation')
table_vs_benchmark = client.po.get_collection('table_vs_benchmark')
image = client.po.get_collection('image')
beta = client.po.get_collection('beta')
client.get_io_loop = asyncio.get_running_loop


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


async def insert_survey(survey_result):
    new_survey = await survey.insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return str(new_survey.inserted_id)


async def get_surveys():
    return await find_all(survey.find({}))


async def insert_portfolio(portfolio_id, portfolio_result):
    result = list(map(problem_encoder_fn, portfolio_result))
    Log.log('saving portfolio: ' + portfolio_id)
    if await portfolio.count_documents({'portfolio_id': portfolio_id}) > 0:
        await portfolio.replace_one({'portfolio_id': portfolio_id}, {
            'portfolio_id': portfolio_id,
            'portfolio': result
        })
    else:
        await portfolio.insert_one({
            'portfolio_id': portfolio_id,
            'portfolio': result
        })


async def save_generation(tag, gen, non_dominated_solutions):
    await generation.insert_one({
        'tag': tag,
        'generation': gen,
        'solutions': non_dominated_solutions
    })


async def get_generation(tag, gen):
    return await generation.find_one({
        'tag': tag,
        'generation': str(gen)
    })


async def save_table_vs_benchmark(tag, t_vs_b):
    await table_vs_benchmark.insert_one({
        'tag': tag,
        'table_vs_benchmark': t_vs_b
    })


async def get_portfolio(portfolio_id):
    return JSONDecoder().decode(MongoJSONEncoder().encode(await portfolio.find_one({'portfolio_id': portfolio_id})))


async def portfolio_exists(portfolio_id):
    return await portfolio.count_documents({'portfolio_id': portfolio_id}) > 0


async def find_all(cursor):
    cursor = cursor.allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results


async def clear_arch2_portfolio(run=0):
    await arch2_portfolio.delete_many({'run': run})


async def insert_arch2_portfolios(run, solutions):
    await arch2_portfolio.insert_many(list(map(lambda p: add_run(run, p), map(problem_encoder_fn, solutions))))


async def get_arch2_portfolios(run=0):
    return await find_all(arch2_portfolio.find({'run': run}))


async def arch2_portfolios_exist(run=0):
    return await arch2_portfolio.count_documents({'run': run}) > 0


async def insert_queue(portfolio_id):
    await queue_status.insert_one({"portfolio_id": portfolio_id, "status": "PUBLISHED"})


async def clear_batch_status():
    await queue_status.delete_one({"portfolio_id": BATCH_TASK_ID})


async def get_queue(portfolio_id):
    return await queue_status.find_one({"portfolio_id": portfolio_id})


async def insert_queue_error(portfolio_id, e):
    await queue_status.replace_one({"portfolio_id": portfolio_id},
                                   {"portfolio_id": portfolio_id, "status": "ERROR", "error": str(e)})


async def insert_queue_complete(portfolio_id):
    await queue_status.replace_one({"portfolio_id": portfolio_id}, {"portfolio_id": portfolio_id, "status": "COMPLETE"})


async def insert_queue_started(portfolio_id):
    await queue_status.replace_one({"portfolio_id": portfolio_id}, {"portfolio_id": portfolio_id, "status": "STARTED"})


async def insert_beta(tag, b):
    await beta.insert_one({
        "tag": tag,
        "beta": b
    })


def add_run(run, problem):
    problem['run'] = run
    return problem


async def min_max(field, min_max_mod):
    data = client.po.get_collection('data')
    return (await find_all(data.find({"data." + field: min_max_mod}, limit=1)))[0]['data']
