import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import json
from django.utils import timezone
from .models import Thread, Message, ChannelBot, ThreadMessage, Document, Vote
from .serializers import MessageSerializer, DocumentSerializer
from llm_orchestrator import router

logger = logging.getLogger(__name__)

# Define the roles for the debate
DEBATE_ROLES = ["Devil's Advocate", "Risk Analisti", "Metrikçi"]

@shared_task
def debate_round(thread_id: int):
    """
    Celery task to run one round of debate in a thread.
    V2: Multiple bots with specific roles respond.
    """
    logger.info(f"Starting debate round V2 for thread_id: {thread_id}")

    try:
        thread = Thread.objects.select_related('channel').get(id=thread_id)
        channel = thread.channel

        # 1. Select bots with specific roles
        active_bots = ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot')

        bots_for_round = []
        for role in DEBATE_ROLES:
            bot_found = active_bots.filter(bot__title=role).first()
            if bot_found:
                bots_for_round.append(bot_found.bot)

        if not bots_for_round:
            logger.warning(f"No special role bots in channel {channel.id} for thread {thread_id}. Ending round.")
            return

        # 2. Get context (last 5 messages)
        recent_messages = Message.objects.filter(thread_associations__thread=thread).order_by('-created_at')[:5]
        llm_messages = [
            {"role": "assistant" if msg.author_type == 'bot' else "user", "content": msg.content_md}
            for msg in reversed(recent_messages)
        ]
        recent_summary = " ".join([msg['content'] for msg in llm_messages]) # Simple summary

        round_messages = []

        # 3. Loop through bots and get responses
        for bot in bots_for_round:
            logger.info(f"Calling orchestrator for bot {bot.name} (Role: {bot.title})")

            # TODO: Use a more sophisticated way to generate stance_hint
            stance_hint = f"Contribute to the discussion from the perspective of a {bot.title}."

            bot_response_content = router.call_llm(
                provider=bot.llm_provider,
                model=bot.llm_model,
                system_prompt=bot.system_prompt,
                messages=llm_messages,
                temperature=bot.temperature,
                # Placeholders for prompt variables
                stance_hint=stance_hint,
                persona_json=str(bot.persona_json),
                source_digest="Not implemented yet.",
                topic=thread.topic,
                recent_summary=recent_summary,
            )

            if not bot_response_content or "Error:" in bot_response_content:
                logger.error(f"Failed to get a valid response from bot {bot.name} for thread {thread_id}.")
                continue

            # 4. Save and broadcast bot's response
            bot_message = Message.objects.create(
                channel=channel,
                author_type='bot',
                author_bot=bot,
                content_md=bot_response_content,
            )
            ThreadMessage.objects.create(thread=thread, message=bot_message)
            round_messages.append(bot_message)
            logger.info(f"Bot {bot.name} responded in thread {thread_id}.")

            channel_layer = get_channel_layer()
            message_data = MessageSerializer(bot_message).data
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {'type': 'message.new', 'message': message_data}
            )

        # --- Voting Step ---
        voting_bots = [b.bot for b in active_bots if b.bot not in bots_for_round]
        if voting_bots and round_messages:
            logger.info(f"Starting voting step with {len(voting_bots)} bots.")

            with open('apps/orchestrator/orchestrator/prompts/vote.txt', 'r') as f:
                vote_prompt_template = f.read()

            for msg in round_messages:
                for voter_bot in voting_bots:
                    logger.info(f"Bot {voter_bot.name} is voting on message {msg.id}")

                    vote_prompt = vote_prompt_template.format(
                        persona_json=str(voter_bot.persona_json),
                        topic=thread.topic,
                        message_to_vote_on=msg.content_md
                    )

                    # We don't need a system prompt or history for this simple vote task
                    vote_response_str = router.call_llm(
                        provider=voter_bot.llm_provider,
                        model=voter_bot.llm_model,
                        system_prompt="You are a voting agent.",
                        messages=[{'role': 'user', 'content': vote_prompt}],
                        temperature=0.2, # Low temp for consistent JSON
                    )

                    try:
                        vote_data = json.loads(vote_response_str)
                        Vote.objects.create(
                            message=msg,
                            voter_bot=voter_bot,
                            value=vote_data.get('vote'),
                            rationale_md=vote_data.get('rationale', '')
                        )
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Could not parse vote from bot {voter_bot.name}: {e}. Response was: {vote_response_str}")

        # Trigger Scribe Summary task
        if round_messages:
            summarize_round.delay(thread_id, [msg.id for msg in round_messages])

        logger.info(f"Completed debate round for thread_id: {thread_id}")
        return f"Debate round for thread {thread_id} complete with {len(bots_for_round)} bots and {len(voting_bots)} voters."

    except Thread.DoesNotExist:
        logger.error(f"Thread with id {thread_id} does not exist.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in debate_round for thread {thread_id}: {e}", exc_info=True)


@shared_task
def summarize_round(thread_id: int, round_message_ids: list[int]):
    """
    Celery task to use the Scribe bot to summarize a round of debate.
    """
    logger.info(f"Starting summarization for thread_id: {thread_id}")

    try:
        thread = Thread.objects.select_related('channel').get(id=thread_id)
        channel = thread.channel

        # 1. Find the Scribe bot
        scribe_bot_assignment = ChannelBot.objects.filter(channel=channel, bot__title="Scribe").select_related('bot').first()
        if not scribe_bot_assignment:
            logger.warning(f"No Scribe bot found in channel {channel.id}. Skipping summarization.")
            return

        scribe_bot = scribe_bot_assignment.bot

        # 2. Get messages from the round
        round_messages = Message.objects.filter(id__in=round_message_ids)
        round_messages_content = "\n\n---\n\n".join(
            [f"**{msg.author_display_name()}**: {msg.content_md}" for msg in round_messages]
        )

        # 3. Call orchestrator with scribe prompt
        with open('apps/orchestrator/orchestrator/prompts/scribe.txt', 'r') as f:
            scribe_prompt_template = f.read()

        scribe_prompt = scribe_prompt_template.format(round_messages=round_messages_content)

        summary_content = router.call_llm(
            provider=scribe_bot.llm_provider,
            model=scribe_bot.llm_model,
            system_prompt="You are a helpful meeting scribe. Your task is to summarize the provided discussion.",
            messages=[{'role': 'user', 'content': scribe_prompt}],
            temperature=0.5,
        )

        if not summary_content or "Error:" in summary_content:
            logger.error(f"Scribe bot {scribe_bot.name} failed to generate a summary for thread {thread_id}.")
            return

        # 4. Save the summary as a new Document
        summary_doc = Document.objects.create(
            channel=channel,
            thread=thread,
            title=f"Summary for: {thread.topic} (Round ending {timezone.now().strftime('%Y-%m-%d %H:%M')})",
            doc_type='summary',
            content_md=summary_content,
            created_by=scribe_bot.created_by # Attributed to the bot's creator
        )
        logger.info(f"Summary document {summary_doc.id} created for thread {thread_id}.")

        # 5. Broadcast the new document
        channel_layer = get_channel_layer()
        doc_data = DocumentSerializer(summary_doc).data
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {'type': 'doc.new', 'document': doc_data}
        )

    except Thread.DoesNotExist:
        logger.error(f"Thread with id {thread_id} does not exist for summarization.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in summarize_round for thread {thread_id}: {e}", exc_info=True)


@shared_task
def generate_consensus(thread_id: int):
    # ... (placeholder)
    pass

@shared_task
def refresh_bot_sources(bot_id: int):
    # ... (placeholder)
    pass
