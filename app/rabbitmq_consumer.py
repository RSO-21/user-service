import pika
import json
import os

from app.database import get_db_session as get_db
from app.models import User

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

def get_connection():
    return pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

def callback(ch, method, properties, body):
    event = json.loads(body.decode("utf-8"))
    tenant_id = event.get("tenant_id", "public")
    
    with get_db(schema=tenant_id) as db:
    
        logger.info(
            "[EVENT:RECEIVED] user_created | user_id=%s username=%s",
            event["user_id"], event["username"]
        )
        try:
            # Idempotency: do not insert twice
            existing = db.query(User).filter(User.id == event["user_id"]).first()
            if existing:
                print(f"User {event['user_id']} already exists")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            user = User(
                id=event["user_id"],          # Keycloak ID
                username=event["username"],
                email=event["email"]
            )

            db.add(user)
            db.commit()

            logger.info(
                "[EVENT:SUCCESS] user created | user_id=%s",
                event["user_id"]
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error processing user_created event: {e}")
            db.rollback()
            # message not acked → will be retried

def start_consumer():
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue="user_created", durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue="user_created",
        on_message_callback=callback
    )

    print("User Service listening for user_created events...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()
