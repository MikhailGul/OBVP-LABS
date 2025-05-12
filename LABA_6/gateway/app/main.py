from fastapi import FastAPI
import aio_pika
from pydantic import BaseModel
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
RABBITMQ_URL = "amqp://admin:admin@rabbitmq:5672"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка OpenTelemetry
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="tempo:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)

class MessageRequest(BaseModel):
    message: str

@app.on_event("startup")
async def startup():
    app.state.connection = await aio_pika.connect_robust(RABBITMQ_URL)
    app.state.channel = await app.state.connection.channel()
    app.state.exchange = await app.state.channel.declare_exchange("messages", aio_pika.ExchangeType.DIRECT)
    app.state.callback_queue = await app.state.channel.declare_queue(exclusive=True)
    app.state.futures = {}

@app.post("/send/")
async def send_message(request: MessageRequest):
    correlation_id = str(uuid.uuid4())
    trace_id = format_trace_id(trace.get_current_span().get_span_context().trace_id)
    payload = {"trace_id": trace_id, "message": request.message}

    with trace.get_tracer(__name__).start_as_current_span("gateway_send_message") as span:
        span.set_attribute("custom.trace_id", trace_id)
        await app.state.exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                reply_to=app.state.callback_queue.name,
                correlation_id=correlation_id
            ),
            routing_key="service_queue"
        )

    with trace.get_tracer(__name__).start_as_current_span("gateway_wait_response"):
        future = asyncio.get_event_loop().create_future()
        app.state.futures[correlation_id] = future
        response = await future
        return json.loads(response.decode())