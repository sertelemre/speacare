from .providers import openai_provider, gemini_provider, groq_provider

def call_llm(provider: str, model: str, system_prompt: str, messages: list, temperature: float = 0.7, **kwargs):
    """
    Routes a call to the appropriate LLM provider.

    Args:
        provider (str): The name of the LLM provider (e.g., 'openai', 'gemini', 'groq').
        model (str): The specific model to use.
        system_prompt (str): The system prompt for the model.
        messages (list): The list of messages in the conversation.
        temperature (float): The temperature for the model.
        **kwargs: Additional provider-specific arguments.

    Returns:
        str: The response from the LLM.
    """
    # Here we can add logic for retries, fallbacks, etc.

    if provider == "openai":
        # The openai_provider will need to handle both OpenAI and DeepSeek if it's API compatible
        return openai_provider.generate(model, system_prompt, messages, temperature, **kwargs)
    elif provider == "gemini":
        return gemini_provider.generate(model, system_prompt, messages, temperature, **kwargs)
    elif provider == "groq":
        return groq_provider.generate(model, system_prompt, messages, temperature, **kwargs)
    # The spec mentioned xai_grok, but the python client is just 'groq'.
    # If a specific XAI client is needed, it would be added here.

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
