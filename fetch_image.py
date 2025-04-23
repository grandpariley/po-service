import asyncio

import db


def main():
    images = asyncio.run(db.get_images())
    for image in images:
        with open(image['filename'], "wb") as image_file:
            image_file.write(image['data'].decode('base64'))

if __name__ == '__main__':
    main()