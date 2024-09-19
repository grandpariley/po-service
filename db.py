import os

import motor.motor_asyncio
from dotenv import load_dotenv

from po.pkg.problem.problem import problem_encoder_fn

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
survey = client.po.get_collection('survey')
data = client.po.get_collection('data')
no_data = client.po.get_collection('no_data')


async def clear_data():
    await data.remove()


async def insert_data(key, d):
    await data.insert_one({'symbol': key, 'data': d})


async def update_data(key, d):
    await data.replace_one({'symbol': key}, {'symbol': key, 'data': d})


async def insert_no_data(nd):
    if await no_data.estimated_document_count({'symbol': nd}) > 0:
        return
    await no_data.insert_one({'symbol': nd})


async def fetch_data():
    data_as_list = find_all(data.find(None))
    data_as_dict = dict()
    for d in data_as_list:
        data_as_dict[d['symbol']] = d['data']
    return data_as_dict


def fetch_no_data(query):
    return find_all(no_data.find(query))


async def insert_survey(survey_result):
    new_survey = await survey.insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return str(new_survey.inserted_id)


async def get_surveys():
    return find_all(survey.find(None))


async def insert_portfolio(portfolio_id, portfolio_result):
    await portfolio.insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': list(map(problem_encoder_fn, portfolio_result))
    })


async def get_portfolio(portfolio_id):
    return await portfolio.find_one({'portfolio_id': portfolio_id})


async def portfolio_exists(portfolio_id):
    return await portfolio.estimated_document_count({'portfolio_id': portfolio_id}) > 0


def find_all(cursor):
    cursor = cursor.allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results
