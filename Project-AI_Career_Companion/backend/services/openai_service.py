import os
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from .keyvault_service import get_secret


# Load configs from env (these will be injected via KeyVault in production)
OPENAI_API_KEY = get_secret("OpenAIKey")
DEPLOYMENT_NAME = "gpt4o"  # replace with actual deployment name

client = AzureOpenAI(api_key=OPENAI_API_KEY)


def call_openai(prompt: str) -> str:
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[{"role": "system", "content": "You are a career planning assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=800
    )
    return response.choices[0].message.content
