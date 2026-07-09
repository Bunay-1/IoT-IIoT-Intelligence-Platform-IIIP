import asyncio
import json
import logging
from datetime import datetime
from typing import Dict

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from src.infrastructure.kafka_ai_integration import KafkaConfig  # Import KafkaConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self):
        self.consumer = None
        self.producer = None
        self.initialize_kafka()
        self.llm = OpenAI(temperature=0.7)  # Initialize LangChain LLM
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""You are a helpful AI assistant for CNC machine operations. Respond to the following query: {query}""",
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def initialize_kafka(self):
        try:
            self.consumer = KafkaConsumer(
                KafkaConfig.TOPIC_CHATBOT_REQUESTS,
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                group_id="chatbot-group",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
            )
            self.producer = KafkaProducer(
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            logger.info("✅ Chatbot Kafka producers and consumers initialized.")
        except NoBrokersAvailable:
            logger.error(
                "❌ No Kafka brokers available. Please ensure Kafka is running."
            )
            # Exit or handle the error appropriately
            exit(1)

    async def _process_request(self, request_data: Dict):
        """
        Process a single chatbot request.
        This is where LangChain integration will happen.
        """
        user_message = request_data.get("message", "No message provided.")
        user_id = request_data.get("user_id", "anonymous")

        logger.info(f"🤖 Chatbot received request from {user_id}: {user_message}")

        # Integrate LangChain here for NLP processing and response generation
        response_message = self.chain.run(query=user_message)

        await self._send_response(user_id, response_message)

    async def _send_response(self, user_id: str, message: str):
        """
        Send a response back to the user via Kafka.
        """
        response_data = {
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.producer.send(KafkaConfig.TOPIC_CHATBOT_RESPONSES, value=response_data)
        logger.info(f"💬 Chatbot sent response to {user_id}: {message}")

    async def start(self):
        """
        Start the chatbot service, listening for requests.
        """
        logger.info("🚀 Chatbot Service started - listening for requests...")
        try:
            while True:
                msg_pack = self.consumer.poll(timeout_ms=1000, max_records=10)

                if not msg_pack:
                    await asyncio.sleep(0.1)
                    continue

                tasks = []
                for topic_partition, messages in msg_pack.items():
                    for message in messages:
                        tasks.append(self._process_request(message.value))

                await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            logger.info("Chatbot Service shutting down...")
        finally:
            if self.consumer:
                self.consumer.close()
            if self.producer:
                self.producer.close()


if __name__ == "__main__":
    # This part is for testing the chatbot service independently
    # In a real deployment, it would be part of the main application loop
    async def main():
        chatbot_service = ChatbotService()
        await chatbot_service.start()

    asyncio.run(main())
