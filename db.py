import json
import os
from json import JSONDecoder

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv

from po.pkg.problem.problem import problem_encoder_fn

load_dotenv()

client: motor.motor_asyncio.AsyncIOMotorClient = None

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def connect_db():
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])


def close_db():
    client.close()


async def insert_survey(survey_result):
    new_survey = await client.po.get_collection('survey').insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return str(new_survey.inserted_id)


async def get_surveys():
    return await find_all(client.po.get_collection('survey').find(None))


async def insert_portfolio(portfolio_id, portfolio_result):
    await client.po.get_collection('portfolio').insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': list(map(problem_encoder_fn, portfolio_result))
    })


async def get_portfolio(portfolio_id):
    return JSONDecoder().decode(MongoJSONEncoder().encode(await client.po.get_collection('portfolio').find_one({'portfolio_id': portfolio_id})))


async def portfolio_exists(portfolio_id):
    return await client.po.get_collection('portfolio').count_documents({'portfolio_id': portfolio_id}) > 0


async def find_all(cursor):
    cursor = cursor.allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results
