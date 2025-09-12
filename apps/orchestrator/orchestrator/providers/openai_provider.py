import os
import openai

# A dictionary to map specific models to their API base URLs if they are not OpenAI's default.
# This allows using OpenAI's client for compatible APIs like DeepSeek.
API_BASES = {
    "deepseek-chat": "https://api.deepseek.com/v1",
    "deepseek-coder": "https://api.deepseek.com/v1",
}

def generate(model: str, system_prompt: str, messages: list, temperature: float = 0.7, **kwargs):
    """
    Generates a response using an OpenAI or compatible model.

    Args:
        model (str): The specific model to use (e.g., 'gpt-4', 'deepseek-chat').
        system_prompt (str): The system prompt for the model.
        messages (list): The list of messages in the conversation.
        temperature (float): The temperature for the model.

    Returns:
        str: The response from the LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = None

    # Check if the model is a special case requiring a different base URL or key.
    if model.startswith("deepseek"):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = API_BASES.get(model)

    if not api_key:
        raise ValueError(f"API key for model {model} is not set in environment variables.")

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    # Format messages for the OpenAI API
    api_messages = [{"role": "system", "content": system_prompt}]

    # Assuming incoming messages are in a standard format like {'role': 'user'/'assistant', 'content': '...'}
    api_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred with the OpenAI provider: {e}")
        # In a real app, you'd want more robust error handling and logging.
        # You might also want to fallback to another provider.
        return f"Error: Could not get a response from {model}."
