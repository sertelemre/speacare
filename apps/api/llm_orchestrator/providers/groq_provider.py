import os
import groq

def generate(model: str, system_prompt: str, messages: list, temperature: float = 0.7, **kwargs):
    """
    Generates a response using a Groq model.
    The Groq API is OpenAI-compatible.

    Args:
        model (str): The specific model to use (e.g., 'llama3-8b-8192').
        system_prompt (str): The system prompt for the model.
        messages (list): The list of messages in the conversation.
        temperature (float): The temperature for the model.

    Returns:
        str: The response from the LLM.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")

    client = groq.Groq(api_key=api_key)

    # Format messages for the API
    api_messages = [{"role": "system", "content": system_prompt}]
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
        print(f"An error occurred with the Groq provider: {e}")
        return f"Error: Could not get a response from {model}."
