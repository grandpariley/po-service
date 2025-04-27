import asyncio
import base64
import os
import uuid

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

def get_random(filename):
    return str(uuid.uuid5(uuid.NAMESPACE_OID, filename))


def main():
    images = asyncio.run(get_images())
    for image in images:
        new_image_filename = image['filename']
        if os.path.exists(new_image_filename):
            new_image_filename = get_random(new_image_filename) + "_" + new_image_filename
        if '/' in new_image_filename:
            directories = new_image_filename[:new_image_filename.find('/')]
            if not os.path.exists(directories):
                os.mkdir(directories)
        with open(new_image_filename, "ab+") as image_file:
            image_file.write(base64.b64decode(image['data']))


if __name__ == '__main__':
    main()
