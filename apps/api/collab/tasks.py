import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Thread, Message, ChannelBot, ThreadMessage
from .serializers import MessageSerializer
from llm_orchestrator import router

logger = logging.getLogger(__name__)

@shared_task
def debate_round(thread_id: int):
    """
    Celery task to run one round of debate in a thread.
    V1: A single bot responds to the last message.
    """
    logger.info(f"Starting debate round for thread_id: {thread_id}")

    try:
        thread = Thread.objects.select_related('channel').get(id=thread_id)
        channel = thread.channel

        # 1. Select a bot
        active_bot_assignment = ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot').first()
        if not active_bot_assignment:
            logger.warning(f"No active bots in channel {channel.id} for thread {thread_id}. Ending round.")
            return

        bot = active_bot_assignment.bot

        # 2. Get context (last 5 messages)
        recent_messages = Message.objects.filter(thread_associations__thread=thread).order_by('-created_at')[:5]

        # Format for LLM
        llm_messages = [
            {"role": "assistant" if msg.author_type == 'bot' else "user", "content": msg.content_md}
            for msg in reversed(recent_messages) # Reverse to get chronological order
        ]

        # 3. Call Orchestrator
        logger.info(f"Calling orchestrator for bot {bot.name} (Model: {bot.llm_provider}/{bot.llm_model})")

        # Note: For a real implementation, we'd use the prompt templates.
        # For this V1, we'll just use the bot's system prompt directly.
        bot_response_content = router.call_llm(
            provider=bot.llm_provider,
            model=bot.llm_model,
            system_prompt=bot.system_prompt,
            messages=llm_messages,
            temperature=bot.temperature,
        )

        if not bot_response_content or "Error:" in bot_response_content:
            logger.error(f"Failed to get a valid response from bot {bot.name} for thread {thread_id}.")
            return

        # 4. Save bot's response as a new message
        bot_message = Message.objects.create(
            channel=channel,
            author_type='bot',
            author_bot=bot,
            content_md=bot_response_content,
        )
        ThreadMessage.objects.create(thread=thread, message=bot_message)
        logger.info(f"Bot {bot.name} responded in thread {thread_id}.")

        # 5. Broadcast the new bot message
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(bot_message).data
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'message.new',
                'message': message_data
            }
        )

        logger.info(f"Completed debate round for thread_id: {thread_id}")
        return f"Debate round for thread {thread_id} complete with bot {bot.name}."

    except Thread.DoesNotExist:
        logger.error(f"Thread with id {thread_id} does not exist.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in debate_round for thread {thread_id}: {e}", exc_info=True)


@shared_task
def generate_consensus(thread_id: int):
    """
    Celery task to generate a consensus document for a thread.
    """
    logger.info(f"Generating consensus for thread_id: {thread_id}")
    # TODO: Fetch all messages and votes for the thread
    # TODO: Call orchestrator with consensus prompt
    # e.g., router.call_llm(...)
    # TODO: Save the output as a Document object
    logger.info(f"Consensus generated for thread_id: {thread_id}")
    return f"Consensus for thread {thread_id} generated."


@shared_task
def refresh_bot_sources(bot_id: int):
    """
    Celery task to refresh a bot's knowledge sources.
    """
    logger.info(f"Refreshing sources for bot_id: {bot_id}")
    # TODO: Fetch bot and its sources
    # TODO: For each source (e.g., URL), re-scrape and update knowledge digest
    # This might involve calling the orchestrator for summarization
    logger.info(f"Sources refreshed for bot_id: {bot_id}")
    return f"Sources for bot {bot_id} refreshed."
