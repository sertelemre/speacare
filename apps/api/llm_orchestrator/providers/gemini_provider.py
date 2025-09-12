import os
import google.generativeai as genai

def generate(model: str, system_prompt: str, messages: list, temperature: float = 0.7, **kwargs):
    """
    Generates a response using a Google Gemini model.

    Args:
        model (str): The specific model to use (e.g., 'gemini-1.5-flash').
        system_prompt (str): The system prompt for the model.
        messages (list): The list of messages in the conversation.
        temperature (float): The temperature for the model.

    Returns:
        str: The response from the LLM.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")

    genai.configure(api_key=api_key)

    # Format messages for the Gemini API
    # Gemini expects a list of {'role': 'user'/'model', 'parts': [text]}
    # The 'system' role is handled differently.
    gemini_messages = []
    for msg in messages:
        role = 'user' if msg['role'] == 'user' else 'model'
        gemini_messages.append({'role': role, 'parts': [msg['content']]})

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        **kwargs
    )

    # The system prompt is passed separately
    gemini_model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
        system_instruction=system_prompt
    )

    try:
        response = gemini_model.generate_content(gemini_messages)
        return response.text
    except Exception as e:
        print(f"An error occurred with the Gemini provider: {e}")
        return f"Error: Could not get a response from {model}."
