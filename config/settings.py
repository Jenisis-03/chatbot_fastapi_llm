import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "Your Key")
client = OpenAI(api_key=OPENAI_API_KEY)

api_enabled = True
try:
    
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Test query"}
        ],
        max_tokens=10,
        timeout=10
    )
    print("OpenAI API key test successful:", test_response.choices[0].message.content)
except OpenAIError as e:
    print("OpenAI API key test failed:", str(e))
    print("Disabling API calls and relying on manual parsing as a last resort.")
    api_enabled = False
except Exception as e:
    print("Unexpected error during OpenAI API test:", str(e))
    print("Disabling API calls and relying on manual parsing as a last resort.")
    api_enabled = False