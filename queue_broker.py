import pika
import os

from po.pkg.log import Log

QUEUE_NAME = "po"


def create():
    rabbitmq.create_queue(QUEUE_NAME)


def publish(message):
    rabbitmq.publish(QUEUE_NAME, message)
    Log.log("Sent message: " + message)


def register_listener(func):
    def callback(ch, method, properties, body):
        body_string = body.decode("utf-8")
        Log.log("Received message: " + body_string)
        func(body_string)

    Log.log("listening...")
    rabbitmq.consume(QUEUE_NAME, callback)


class RabbitMQ:
    def __init__(self):
        self.user = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
        self.password = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def create_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def consume(self, queue_name, callback):
        if not self.channel:
            raise Exception("Connection is not established.")
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()

    def publish(self, queue_name, message):
        if not self.channel:
            raise Exception("Connection is not established.")
        self.channel.queue_declare(queue=queue_name)
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,
                                   ))


rabbitmq = RabbitMQ()
