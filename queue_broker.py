import pika
import os

from pika.exceptions import AMQPConnectionError

from po.pkg.log import Log

QUEUE_NAME = "po"

def publish(message):
    rabbitmq.publish(QUEUE_NAME, message)
    Log.log("Sent message: " + message)


def register_listener(func):
    def callback(ch, method, properties, body):
        Log.log("Received message: " + body)
        func(body)

    # rabbitmq.consume(QUEUE_NAME, callback)


class RabbitMQ:
    def __init__(self):
        self.user = os.getenv('RABBITMQ_USER', 'user')
        self.password = os.getenv('RABBITMQ_PASSWORD', 'password')
        self.host = os.getenv('RABBITMQ_HOST', 'po-rabbitmq')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.connection = None
        self.channel = None
        try:
            self.connect()
        except AMQPConnectionError as e:
            print(e)

    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

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
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.basic_publish(exchange='',
                                   routing_key=queue_name,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,
                                   ))
        print(f"Sent message to queue {queue_name}: {message}")

rabbitmq = RabbitMQ()