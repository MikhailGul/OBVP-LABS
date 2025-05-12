import asyncio
import aio_pika
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server, Counter, Histogram

RABBITMQ_URL = "amqp://admin:admin@rabbitmq:5672"
MESSAGES_PROCESSED = Counter("messages_processed_total", "Total number of messages processed")
MESSAGE_PROCESSING_TIME = Histogram("message_processing_duration_seconds", "Time spent processing message")

# Настройка OpenTelemetry
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="tempo:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

async def main():
    start_http_server(8001)
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("messages", aio_pika.ExchangeType.DIRECT)
    queue = await channel.declare_queue("service_queue", durable=True)
    await queue.bind(exchange, routing_key="service_queue")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            start_time = time.time()
            try:
                incoming_data = json.loads(message.body)
                trace_id = incoming_data.get("trace_id")
                incoming_message = incoming_data.get("message")

                with trace.get_tracer(__name__).start_as_current_span("service_process_message") as span:
                    span.set_attribute("custom.trace_id", trace_id)
                    response_text = f"Processed: {incoming_message.upper()}"

                    if message.reply_to:
                        response_payload = {"trace_id": trace_id, "result": response_text}
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=json.dumps(response_payload).encode(),
                                correlation_id=message.correlation_id
                            ),
                            routing_key=message.reply_to
                        )

                MESSAGES_PROCESSED.inc()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
            finally:
                MESSAGE_PROCESSING_TIME.observe(time.time() - start_time)

if __name__ == "__main__":
    asyncio.run(main())