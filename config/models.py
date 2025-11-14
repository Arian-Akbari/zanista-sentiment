import os
import warnings

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

load_dotenv()

required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_ENDPOINT"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    warnings.warn(f"Missing environment variables: {', '.join(missing)}")

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)


def get_client() -> AzureOpenAI:
    return client


def get_async_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
