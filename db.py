import os

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv

from pomatch.pkg.response import ResponseJSONEncoder

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
survey = client.po.get_collection('survey')


async def insert_survey(survey_result):
    new_survey = await survey.insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return ResponseJSONEncoder().encode(new_survey.inserted_id).replace('"', '')


async def get_surveys():
    cursor = survey.find(None).allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results

async def insert_portfolio(portfolio_id, portfolio_result):
    await portfolio.insert_one({
        '_id': ObjectId(portfolio_id),
        'portfolio': portfolio_result
    })


async def portfolio_exists(portfolio_id):
    return await portfolio.estimated_document_count({'_id': ObjectId(portfolio_id)}) > 0


async def get_portfolio(portfolio_id):
    response = await portfolio.find_one({'_id': ObjectId(portfolio_id)})
    return ResponseJSONEncoder().encode(response)
