import asyncio
import json
import os
from json import JSONDecoder

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv

from po.pkg.problem.problem import problem_encoder_fn

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
arch2_portfolio = client.po.get_collection('arch2_portfolio')
survey = client.po.get_collection('survey')
queue_status = client.po.get_collection('queue')
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
    return await find_all(survey.find(None))


async def insert_portfolio(portfolio_id, portfolio_result):
    print('saving portfolio: ' + portfolio_id + ' with results of length ' + str(len(portfolio_result['variables'])))
    await portfolio.insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': list(map(problem_encoder_fn, portfolio_result))
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


async def clear_arch2_portfolio():
    await arch2_portfolio.delete_many({})


async def insert_arch2_portfolios(solutions):
    print('saving ' + str(len(solutions)) + ' solutions')
    await arch2_portfolio.insert_many(list(map(problem_encoder_fn, solutions)))


async def get_arch2_portfolios():
    return await find_all(arch2_portfolio.find(None))


async def arch2_portfolios_exist():
    return await arch2_portfolio.count_documents({}) > 0


async def insert_queue(portfolio_id):
    await queue_status.insert_one({"portfolio_id": portfolio_id, "status": "PUBLISHED"})


async def get_queue(portfolio_id):
    return await queue_status.find_one({"portfolio_id": portfolio_id})


async def insert_queue_error(portfolio_id, e):
    await queue_status.replace_one({"portfolio_id": portfolio_id},
                                   {"portfolio_id": portfolio_id, "status": "ERROR", "error": str(e)})


async def insert_queue_complete(portfolio_id):
    await queue_status.replace_one({"portfolio_id": portfolio_id}, {"portfolio_id": portfolio_id, "status": "COMPLETE"})


async def insert_queue_started(portfolio_id):
    await queue_status.replace_one({"portfolio_id": portfolio_id}, {"portfolio_id": portfolio_id, "status": "STARTED"})
