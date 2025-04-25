import asyncio
import base64
import os
import motor.motor_asyncio
from dotenv import load_dotenv

from po.pkg.log import Log

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
image_collection = client.po.get_collection('image')


async def find_all(cursor):
    cursor = cursor.allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results


async def get_images():
    return await find_all(image_collection.find({}))


async def insert_image(filename, data_bytes):
    Log.log("inserting image into db: " + filename)
    await image_collection.insert_one({
        'filename': filename,
        'data': data_bytes
    })


def main():
    images = asyncio.run(get_images())
    for image in images:
        with open(image['filename'], "wb") as image_file:
            image_file.write(image['data'].decode('base64'))


if __name__ == '__main__':
    main()
