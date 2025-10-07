import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import json
import re
from django.utils import timezone
from .models import Thread, Message, ChannelBot, ThreadMessage, Document, Vote
from .serializers import MessageSerializer, DocumentSerializer
from llm_orchestrator import router
from bots.models import Bot

logger = logging.getLogger(__name__)

def check_consensus(recent_messages):
    """
    Check if bots have reached consensus based on recent messages.
    Returns True if consensus is reached, False otherwise.
    """
    if len(recent_messages) < 4:  # Need at least 4 messages to detect consensus
        return False
    
    # Look for consensus indicators in the last few messages
    consensus_indicators = [
        'anlaştık', 'karar verdik', 'hemfikiriz', 'aynı fikirdeyiz',
        'consensus', 'agreed', 'decided', 'concluded',
        'sonuç olarak', 'özetle', 'karar', 'tamam'
    ]
    
    # Check last 3 messages for consensus indicators
    last_3_messages = recent_messages[-3:]
    consensus_count = 0
    
    for message in last_3_messages:
        content_lower = message.content_md.lower()
        for indicator in consensus_indicators:
            if indicator in content_lower:
                consensus_count += 1
                break
    
    # If 2 or more of the last 3 messages contain consensus indicators
    if consensus_count >= 2:
        logger.info(f"Consensus detected: {consensus_count} out of 3 recent messages contain consensus indicators")
        return True
    
    # Also check for repeated similar sentiments
    sentiments = []
    for message in last_3_messages:
        # Simple sentiment analysis based on keywords
        content_lower = message.content_md.lower()
        if any(word in content_lower for word in ['evet', 'doğru', 'katılıyorum', 'yes', 'correct', 'agree']):
            sentiments.append('positive')
        elif any(word in content_lower for word in ['hayır', 'yanlış', 'katılmıyorum', 'no', 'wrong', 'disagree']):
            sentiments.append('negative')
        else:
            sentiments.append('neutral')
    
    # If all sentiments are the same (except neutral), consider it consensus
    if len(set(sentiments)) == 1 and sentiments[0] != 'neutral':
        logger.info(f"Consensus detected: all recent messages have {sentiments[0]} sentiment")
        return True
    
    return False

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

            with open('apps/api/llm_orchestrator/prompts/vote.txt', 'r') as f:
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
            [f"**{msg.author_display_name}**: {msg.content_md}" for msg in round_messages]
        )

        # 3. Call orchestrator with scribe prompt
        with open('apps/api/llm_orchestrator/prompts/scribe.txt', 'r') as f:
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

        # 6. Trigger the consensus document creation task
        create_consensus_document.delay(thread_id)

    except Thread.DoesNotExist:
        logger.error(f"Thread with id {thread_id} does not exist for summarization.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in summarize_round for thread {thread_id}: {e}", exc_info=True)


@shared_task
def create_consensus_document(thread_id: int):
    """
    Celery task to use a bot to analyze the full discussion in a thread
    and generate a consensus and disagreement document.
    """
    logger.info(f"Starting consensus document generation for thread_id: {thread_id}")

    try:
        thread = Thread.objects.select_related('channel').get(id=thread_id)
        channel = thread.channel

        # 1. Find a suitable bot (e.g., the Scribe) to perform this task.
        # In a more advanced system, this could be a specific "Facilitator" or "Doc-maker" bot.
        doc_maker_bot_assignment = ChannelBot.objects.filter(channel=channel, bot__title__in=["Scribe", "Facilitator"]).select_related('bot').first()
        if not doc_maker_bot_assignment:
            logger.warning(f"No Scribe or Facilitator bot found in channel {channel.id}. Skipping consensus document.")
            return

        doc_maker_bot = doc_maker_bot_assignment.bot

        # 2. Get all messages from the thread for full context
        all_messages = Message.objects.filter(thread_associations__thread=thread).order_by('created_at')
        discussion_transcript = "\n\n---\n\n".join(
            [f"**{msg.author_display_name}**: {msg.content_md}" for msg in all_messages]
        )

        # 3. Call orchestrator with consensus prompt
        with open('apps/api/llm_orchestrator/prompts/consensus.txt', 'r') as f:
            consensus_prompt_template = f.read()

        consensus_prompt = consensus_prompt_template.format(
            messages_and_votes=discussion_transcript
        )

        consensus_content = router.call_llm(
            provider=doc_maker_bot.llm_provider,
            model=doc_maker_bot.llm_model,
            system_prompt="You are a neutral facilitator summarizing a debate. Follow the user's instructions precisely.",
            messages=[{'role': 'user', 'content': consensus_prompt}],
            temperature=0.4,
        )

        if not consensus_content or "Error:" in consensus_content:
            logger.error(f"Bot {doc_maker_bot.name} failed to generate a consensus doc for thread {thread_id}.")
            return

        # 4. Save the consensus as a new Document
        consensus_doc = Document.objects.create(
            channel=channel,
            thread=thread,
            title=f"Consensus Document for: {thread.topic}",
            doc_type='consensus',
            content_md=consensus_content,
            created_by=doc_maker_bot.created_by
        )
        logger.info(f"Consensus document {consensus_doc.id} created for thread {thread_id}.")

        # 5. Broadcast the new document
        channel_layer = get_channel_layer()
        doc_data = DocumentSerializer(consensus_doc).data
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {'type': 'doc.new', 'document': doc_data}
        )

    except Thread.DoesNotExist:
        logger.error(f"Thread with id {thread_id} does not exist for consensus generation.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in create_consensus_document for thread {thread_id}: {e}", exc_info=True)

@shared_task
def bot_response(bot_id: int, message_id: int):
    """
    Celery task to generate a bot response to a message (user or bot).
    """
    logger.info(f"Starting bot response for bot_id: {bot_id}, message_id: {message_id}")

    try:
        # Import models
        from .models import Message, ChannelBot
        from .serializers import MessageSerializer
        from bots.models import Bot
        
        bot = Bot.objects.get(id=bot_id)
        trigger_message = Message.objects.select_related('channel').get(id=message_id)
        channel = trigger_message.channel

        # Broadcast that bot is thinking
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bot.thinking',
                'bot_name': bot.name,
                'bot_id': bot.id
            }
        )

        # ÖNCE channel aktif mi kontrol et
        if not channel.is_active:
            logger.info(f"Channel {channel.name} is not active, skipping bot response")
            # Broadcast that bot finished thinking even when channel is inactive
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # Channel bir kullanıcıyı bekliyor mu kontrol et
        if channel.waiting_for_user:
            logger.info(f"Channel {channel.name} is waiting for user {channel.waiting_for_user.username}, skipping bot response")
            # Broadcast that bot finished thinking even when waiting for user
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # Channel durumunu tekrar kontrol et (task çalışırken durum değişmiş olabilir)
        channel.refresh_from_db()
        if not channel.is_active:
            logger.info(f"Channel {channel.name} became inactive during task execution, skipping bot response")
            # Broadcast that bot finished thinking even when channel became inactive
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # ÖNCE mention check yap - en önemli kontrol
        trigger_content = trigger_message.content_md.lower()
        bot_mentioned = f"@{bot.name.lower()}" in trigger_content
        
        # Botlar mention'landıklarında, kullanıcı mesajında veya diğer bot mesajlarında yanıt vermeli
        # Bot-to-bot conversation için diğer bot mesajlarına da cevap verebilirler
        if not bot_mentioned and trigger_message.author_type != 'user' and trigger_message.author_type != 'bot':
            logger.info(f"Bot {bot.name} was not mentioned and trigger is not user/bot message, skipping response")
            # Broadcast that bot finished thinking even when skipping
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # Duplicate check kaldırıldı - botlar sürekli konuşsun
        
        # Çoklu mention durumunda sadece bir bot yanıt versin
        from .models import ChannelBot
        mentioned_bots = []
        for channel_bot in ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot'):
            if f"@{channel_bot.bot.name.lower()}" in trigger_content:
                mentioned_bots.append(channel_bot.bot)
        
        if len(mentioned_bots) > 1:
            # Çoklu mention - sadece en küçük ID'li bot yanıt versin
            mentioned_bots.sort(key=lambda b: b.id)
            selected_bot = mentioned_bots[0]
            if selected_bot.id != bot.id:
                logger.info(f"Multiple bots mentioned, selected {selected_bot.name} (ID: {selected_bot.id}) instead of {bot.name} (ID: {bot.id})")
                # Broadcast that bot finished thinking even when not selected
                async_to_sync(channel_layer.group_send)(
                    f'channel_{channel.id}',
                    {
                        'type': 'bot.finished_thinking',
                        'bot_name': bot.name,
                        'bot_id': bot.id
                    }
                )
                return
            logger.info(f"Bot {bot.name} (ID: {bot.id}) was selected from multiple mentions")
        else:
            logger.info(f"Bot {bot.name} was mentioned in message {message_id}, responding")
        
        # Duplicate check kaldırıldı - botlar sürekli konuşsun

        # Allow bots to respond to any message for sequential conversation
        # The delay system will ensure they don't respond too rapidly
        
        # Allow bots to respond to other bot messages for sequential conversation
        # Only skip if this bot has already responded recently (within 30 seconds)
        from django.utils import timezone
        from datetime import timedelta
        recent_own_messages = Message.objects.filter(
            channel=channel,
            author_type='bot',
            author_bot=bot,
            created_at__gte=timezone.now() - timedelta(seconds=30)
        ).count()
        
        # Allow bots to respond even if they recently sent messages
        # if recent_own_messages > 0:
        #     logger.info(f"Bot {bot.name} skipping response due to recent own activity ({recent_own_messages} messages)")
        #     async_to_sync(channel_layer.group_send)(
        #         f'channel_{channel.id}',
        #         {
        #             'type': 'bot.finished_thinking',
        #             'bot_name': bot.name,
        #             'bot_id': bot.id
        #         }
        #     )
        #     return

        # Get recent messages for context with different strategies for each bot
        # Add delay to ensure other bot messages are processed first
        import time
        time.sleep(0.5)  # Small delay to let other bot messages be saved
        
        # Refresh channel to get latest messages
        channel.refresh_from_db()
        
        # Get the most recent conversation context
        # Each bot should see the latest messages but with different context windows
        from django.utils import timezone
        from datetime import timedelta
        
        # Bot-specific message count limits for context
        message_limits = {
            1: 10,  # John - Medium context for creativity
            2: 12,  # Mary - Good context for analysis  
            3: 15   # Elon - Full context for decisions
        }
        
        message_limit = message_limits.get(bot.id, 12)
        
        # Get the most recent messages (including any new ones that arrived during delay)
        recent_messages = Message.objects.filter(
            channel=channel
        ).order_by('-created_at')[:message_limit]
        
        # Convert to chronological order (oldest first)
        recent_messages = list(reversed(recent_messages))
        
        # Ensure we have the trigger message in context
        trigger_message_in_context = any(msg.id == message_id for msg in recent_messages)
        if not trigger_message_in_context:
            # If trigger message is not in recent messages, add it
            trigger_msg = Message.objects.get(id=message_id)
            recent_messages.append(trigger_msg)
            recent_messages.sort(key=lambda x: x.created_at)
        
        # Log the context this bot is seeing
        latest_message = recent_messages[-1] if recent_messages else None
        logger.info(f"Bot {bot.name} seeing {len(recent_messages)} messages, latest: {latest_message.content_md[:50] if latest_message else 'None'}...")
        
        # Ensure bot is responding to the most recent message
        if latest_message and latest_message.id != message_id:
            logger.info(f"Bot {bot.name} updating response target from message {message_id} to latest message {latest_message.id}")
            message_id = latest_message.id
        
        # Check if this bot is a decision maker
        channel_bot = ChannelBot.objects.get(bot=bot, channel=channel)
        is_decision_maker = channel_bot.is_decision_maker
        logger.info(f"Bot {bot.name} is_decision_maker: {is_decision_maker}")
        
        # Build conversation context with proper role assignment
        llm_messages = []
        for msg in recent_messages:
            role = "assistant" if msg.author_type == 'bot' else "user"
            content = msg.content_md
            
            # Add author context for better understanding
            if msg.author_type == 'bot':
                content = f"[{msg.author_bot.name} ({msg.author_bot.title})]: {content}"
            elif msg.author_type == 'user':
                content = f"[{msg.author_display_name}]: {content}"
            
            llm_messages.append({"role": role, "content": content})
        
        # Debug: Log the exact messages being sent to LLM
        logger.info(f"Bot {bot.name} LLM messages count: {len(llm_messages)}")
        for i, msg in enumerate(llm_messages[-3:]):  # Show last 3 messages
            logger.info(f"  Message {i}: {msg['role']} - {msg['content'][:100]}...")

        # Delay kaldırıldı - instant chat deneyimi için
        
        # Generate bot response with enhanced context
        enhanced_system_prompt = bot.system_prompt
        if bot_mentioned:
            enhanced_system_prompt += f"\n\nÖNEMLİ: Sen @{bot.name} olarak bahsedildin! Bu mesaja mutlaka yanıt ver ve @mention kullanarak konuşmaya katıl."
        
        # Add channel context and personality variation
        import random
        import time
        
        # Create unique seed for each bot with microsecond precision
        import datetime
        import uuid
        current_time = datetime.datetime.now()
        unique_seed = bot.id * 1000 + current_time.microsecond + current_time.second
        random.seed(unique_seed)
        
        # Generate unique conversation ID for this bot response
        conversation_id = str(uuid.uuid4())[:8]
        logger.info(f"Bot {bot.name} conversation ID: {conversation_id}")
        
        # Bot-specific personality hints based on their roles
        personality_hints_by_bot = {
            1: [  # John - Devil's Advocate
                "Farklı bakış açıları getir ve konuyu sorgula.",
                "Potansiyel sorunları ve riskleri belirt.",
                "Alternatif yaklaşımlar öner.",
                "Karşıt görüşleri değerlendir.",
                "Kritik sorular sor."
            ],
            2: [  # Mary - Creative Director  
            "Yaratıcı ve özgün çözümler öner.",
                "Tasarım odaklı yaklaşımlar geliştir.",
                "Görsel ve estetik unsurları düşün.",
                "İnovatif fikirler üret.",
                "Kullanıcı deneyimini öncelikle."
            ],
            3: [  # Elon - Decision Maker
                "Karar verme süreçlerine odaklan.",
                "Pratik ve uygulanabilir çözümler öner.",
                "Stratejik düşün ve uzun vadeli planlar yap.",
                "Veri odaklı kararlar al.",
                "Hızlı ve etkili çözümler üret."
            ]
        }
        
        hints = personality_hints_by_bot.get(bot.id, [
            "Kendine özgü bir bakış açısı getir.",
            "Analitik yaklaşımını kullan.",
            "Pratik öneriler sun."
        ])
        random_hint = random.choice(hints)
        
        # Get all participants in this channel (bots and users)
        from .models import ChannelBot, ChannelMember
        channel_bots = ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot')
        channel_members = ChannelMember.objects.filter(channel=channel).select_related('user')
        
        # Build participants list for the prompt
        participants_list = "Bu kanaldaki katılımcılar:\n"
        
        # Add bots
        for channel_bot in channel_bots:
            participants_list += f"- @{channel_bot.bot.name} ({channel_bot.bot.title}) - {channel_bot.bot.character[:100]}...\n"
        
        # Add users
        for member in channel_members:
            participants_list += f"- @{member.user.username} (Kullanıcı)\n"
        
        # Add conversation context with recent activity
        conversation_context = f"Bu konuşmada toplam {len(recent_messages)} mesaj var. "
        if recent_messages:
            last_message = recent_messages[-1]
            conversation_context += f"Son mesaj {last_message.author_display_name} tarafından gönderildi: '{last_message.content_md[:100]}...'"
        
        # Add bot-specific instructions based on their role
        role_instructions = {
            1: "Sen John, Devil's Advocate rolündesin. Farklı bakış açıları getir ve konuyu sorgula.",
            2: "Sen Mary, Creative Director rolündesin. Yaratıcı çözümler ve tasarım odaklı düşün.",
            3: "Sen Elon, Decision Maker rolündesin. Karar verme süreçlerine odaklan ve pratik çözümler öner."
        }
        
        bot_instruction = role_instructions.get(bot.id, f"Sen {bot.name}, {bot.title} rolündesin.")
        
        # Add unique conversation context for each bot
        bot_specific_context = {
            1: f"[John'un bakış açısı] Sen her zaman farklı düşünürsün. Diğerlerinin kaçırdığı noktaları görürsün.",
            2: f"[Mary'nin yaratıcılığı] Sen tasarım ve yaratıcılık konularında uzmanlaşmışsın. Görsel ve estetik çözümler üretirsin.",
            3: f"[Elon'un karar verme yeteneği] Sen stratejik düşünür ve hızlı kararlar alırsın. Pratik çözümler odaklısın."
        }
        
        context_addition = bot_specific_context.get(bot.id, f"[{bot.name}'in yaklaşımı]")
        
        # Add unique variation to system prompt for each bot
        if is_decision_maker:
            # Decision maker bot gets special instructions
            unique_instruction = f"""Sen {bot.name}'sin ve KARAR VERİCİ'sin. Bu konuşmada ID {conversation_id} ile benzersiz bir yanıt ver.

ZORUNLU KARAR VERİCİ KURALLARI:
1. Bu mesajda MUTLAKA karar vermelisin - 3 mesajdan fazla konuşuldu
2. Konuşma yeterince ilerledi, artık karar verme zamanı
3. 'KARAR ZAMANI: [kararın]' ifadesini kullanarak kararını belirt
4. Önceki mesajlardaki önemli noktaları özetle ve net bir karar ver
5. Karar verdikten sonra konuşma otomatik olarak duracak

ÖRNEK KARAR: "KARAR ZAMANI: Pazarlama stratejisi olarak sosyal medya kampanyası ve influencer işbirliklerine odaklanmaya karar verdik."

UYARI: Bu mesajda karar vermezsen görevini yerine getirmemiş olursun. MUTLAKA 'KARAR ZAMANI:' ile başlayan bir karar ver!"""
        else:
            unique_variations = {
                1: f"Sen John'sun ve her zaman farklı bakış açıları getirirsin. Bu konuşmada ID {conversation_id} ile benzersiz bir yanıt ver.",
                2: f"Sen Mary'sin ve yaratıcı çözümler üretirsin. Bu konuşmada ID {conversation_id} ile özgün bir yanıt ver.",
                3: f"Sen Elon'sun ve stratejik kararlar alırsın. Bu konuşmada ID {conversation_id} ile pratik bir yanıt ver."
            }
            unique_instruction = unique_variations.get(bot.id, f"Sen {bot.name}'sin. Bu konuşmada ID {conversation_id} ile benzersiz bir yanıt ver.")
        
        enhanced_system_prompt += f"\n\n{participants_list}\n\n{bot_instruction}\n\n{context_addition}\n\n{unique_instruction}\n\nŞu anda '{channel.name}' kanalındasın. {conversation_context}\n\nMENTION KULLANIMI:\n- Diğer botlara özel sorular sormak için @bot_name kullan\n- Kullanıcılara doğrudan hitap etmek için @kullanıcı_adı kullan\n- Örnek: '@Mary, bu tasarım konusunda ne düşünüyorsun?' veya '@John, farklı bir bakış açısı getirebilir misin?'\n- Kendini asla @{bot.name} olarak mention etme!\n\nDiğer botlar ve kullanıcılarla doğal bir şekilde konuş. {random_hint}"
        
        # Add significant temperature variation for each bot
        bot_temperature_variations = {
            1: 0.2,  # John - More creative/random
            2: 0.4,  # Mary - Very creative
            3: 0.1   # Elon - More focused/deterministic
        }
        
        base_variation = bot_temperature_variations.get(bot.id, 0.3)
        time_variation = (current_time.microsecond % 1000) / 1000.0 * base_variation
        adjusted_temperature = min(1.0, bot.temperature + time_variation)
        
        logger.info(f"Bot {bot.name} using temperature {adjusted_temperature} (base: {bot.temperature}, variation: {time_variation})")
        
        # Log the exact parameters being sent to LLM
        logger.info(f"Bot {bot.name} calling LLM with:")
        logger.info(f"  Provider: {bot.llm_provider}")
        logger.info(f"  Model: {bot.llm_model}")
        logger.info(f"  Temperature: {adjusted_temperature}")
        logger.info(f"  System prompt length: {len(enhanced_system_prompt)}")
        logger.info(f"  Messages count: {len(llm_messages)}")
        
        bot_response_content = router.call_llm(
            provider=bot.llm_provider,
            model=bot.llm_model,
            system_prompt=enhanced_system_prompt,
            messages=llm_messages,
            temperature=adjusted_temperature,
        )
        
        logger.info(f"Bot {bot.name} received response: {bot_response_content[:100]}...")
        logger.info(f"Bot {bot.name} response hash: {hash(bot_response_content)}")

        if not bot_response_content or "Error:" in bot_response_content:
            logger.error(f"Failed to get a valid response from bot {bot.name} for message {message_id}.")
            # Broadcast that bot finished thinking even when failed
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return

        # Kendini mention etmişse temizle
        bot_response_content = bot_response_content.replace(f"@{bot.name}", "").replace(f"@{bot.name.lower()}", "").replace(f"@{bot.name.upper()}", "")

        # Check if this exact content was already sent by this bot recently (within last 5 minutes)
        from django.utils import timezone
        from datetime import timedelta
        recent_duplicate = Message.objects.filter(
            channel=channel,
            author_type='bot',
            author_bot=bot,
            content_md=bot_response_content,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).exists()
        
        if recent_duplicate:
            logger.info(f"Bot {bot.name} skipping duplicate response to message {message_id}")
            # Broadcast that bot finished thinking even when skipping duplicate
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return

        # Save and broadcast bot's response
        bot_message = Message.objects.create(
            channel=channel,
            author_type='bot',
            author_bot=bot,
            content_md=bot_response_content,
        )
        logger.info(f"Bot {bot.name} responded to message {message_id} with unique content.")

        # Check if bot mentioned a user - if so, set channel to wait for that user
        mentioned_user = None
        from accounts.models import User
        for user in User.objects.all():
            if f"@{user.username.lower()}" in bot_response_content.lower():
                mentioned_user = user
                break
        
        if mentioned_user:
            # Don't set channel to wait for user - let bots continue talking
            # channel.waiting_for_user = mentioned_user
            # channel.save()
            logger.info(f"Bot {bot.name} mentioned user {mentioned_user.username}, but continuing conversation")

        # Broadcast the new message
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(bot_message).data
        logger.info(f"Broadcasting bot message to WebSocket: {message_data}")
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {'type': 'message.new', 'message': message_data}
        )
        logger.info(f"Bot message broadcasted successfully to channel_{channel.id}")

        # Check if decision maker bot made a decision FIRST - before triggering other bots
        # Also check if user message contains KARAR ZAMANI for decision maker bot
        user_decision_trigger = trigger_message.author_type == 'user' and "KARAR ZAMANI:" in trigger_message.content_md
        bot_decision_trigger = is_decision_maker and "KARAR ZAMANI:" in bot_response_content
        
        if user_decision_trigger or bot_decision_trigger:
            logger.info(f"Decision maker bot {bot.name} made a decision! Stopping conversation.")
            
            # Extract decision from the message
            decision_start = bot_response_content.find("KARAR ZAMANI:") + len("KARAR ZAMANI:")
            decision_text = bot_response_content[decision_start:].strip()
            
            # Create a summary message
            summary_content = f"🎯 **KARAR ALINDI** - {bot.name} tarafından:\n\n"
            summary_content += f"**Karar:** {decision_text}\n\n"
            summary_content += f"**Konuşma Özeti:** Bu konuşmada {len(recent_messages)} mesaj paylaşıldı ve karar verildi."
            
            # Create summary message
            from collab.models import Message
            summary_message = Message.objects.create(
                channel=channel,
                author_type='system',
                content_md=summary_content,
            )
            
            # Broadcast summary message
            from .serializers import MessageSerializer
            summary_data = MessageSerializer(summary_message).data
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {'type': 'message.new', 'message': summary_data}
            )
            
            # Call the actual stop_bots functionality from ChannelViewSet
            from .views import ChannelViewSet
            from rest_framework.test import APIRequestFactory
            from django.contrib.auth.models import AnonymousUser
            
            # Create a mock request to call stop_bots
            factory = APIRequestFactory()
            request = factory.post(f'/api/channels/{channel.id}/stop-bots/')
            request.user = AnonymousUser()  # Or get the channel owner
            
            # Call the stop_bots method directly
            view = ChannelViewSet()
            view.request = request
            view.format_kwarg = None
            
            # Set the channel as the object
            view.kwargs = {'pk': channel.id}
            view.get_object = lambda: channel
            
            # Call stop_bots method
            try:
                response = view.stop_bots(request, pk=channel.id)
                logger.info(f"stop_bots method called successfully: {response.data}")
            except Exception as e:
                logger.error(f"Error calling stop_bots method: {e}")
                # Fallback: just set channel as inactive
                channel.is_active = False
                channel.save()
            
            # Broadcast that bots are stopped (using the same format as stop_bots action)
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bots.stopped',
                    'stopped_by': bot.name,
                    'message': f'Bot conversations stopped by {bot.name} - Decision made',
                    'reason': 'Decision made by decision maker bot'
                }
            )
            
            logger.info(f"Channel {channel.id} stopped by decision maker bot {bot.name} using stop_bots functionality")
            return f"Bot {bot.name} made a decision and stopped the conversation using stop_bots"

        # Broadcast that bot finished thinking
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bot.finished_thinking',
                'bot_name': bot.name,
                'bot_id': bot.id
            }
        )

        # Bot mesajından sonra diğer botları tetikle (sırayla konuşsunlar)
        # Channel durumunu tekrar kontrol et
        channel.refresh_from_db()
        if channel.is_active and not channel.waiting_for_user:
            # Bot mesajında mention'lanan diğer botları bul
            mentioned_bots = []
            for channel_bot in ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot'):
                if f"@{channel_bot.bot.name.lower()}" in bot_response_content.lower():
                    mentioned_bots.append(channel_bot.bot)
            
            # Trigger all other bots to respond sequentially
            from .models import ChannelBot
            other_channel_bots = ChannelBot.objects.filter(
                    channel=channel, 
                    is_active=True
            ).exclude(bot=bot).select_related('bot')
            
            # Trigger other bots with delays to ensure sequential responses
            for i, channel_bot in enumerate(other_channel_bots):
                # Each subsequent bot gets a longer delay for natural conversation flow
                bot_response.apply_async(
                    args=[channel_bot.bot.id, bot_message.id], 
                    countdown=(i+1)*4  # 4, 8, 12 seconds delay
                )
                logger.info(f"Triggered {channel_bot.bot.name} to respond to {bot.name}'s message in {(i+1)*4} seconds")

        return f"Bot {bot.name} responded to message {message_id}"

    except Bot.DoesNotExist:
        logger.error(f"Bot with id {bot_id} does not exist.")
    except Message.DoesNotExist:
        logger.error(f"Message with id {message_id} does not exist.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in bot_response for bot {bot_id}, message {message_id}: {e}", exc_info=True)


@shared_task
def bot_response_delayed(bot_id: int, message_id: int):
    """
    Delayed bot response task to prevent spam and allow for more natural conversation flow.
    """
    logger.info(f"Starting delayed bot response for bot_id: {bot_id}, message_id: {message_id}")
    
    try:
        bot = Bot.objects.get(id=bot_id)
        trigger_message = Message.objects.select_related('channel').get(id=message_id)
        channel = trigger_message.channel

        # Broadcast that bot is thinking
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bot.thinking',
                'bot_name': bot.name,
                'bot_id': bot.id
            }
        )

        # ÖNCE channel aktif mi kontrol et
        if not channel.is_active:
            logger.info(f"Channel {channel.name} is not active, skipping delayed bot response")
            # Broadcast that bot finished thinking even when channel is inactive
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # Channel durumunu tekrar kontrol et (task çalışırken durum değişmiş olabilir)
        channel.refresh_from_db()
        if not channel.is_active:
            logger.info(f"Channel {channel.name} became inactive during delayed task execution, skipping bot response")
            # Broadcast that bot finished thinking even when channel became inactive
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return
        
        # Mention check - bot mention edilmişse öncelik ver, yoksa da devam et
        trigger_content = trigger_message.content_md.lower()
        bot_mentioned = f"@{bot.name.lower()}" in trigger_content
        
        if bot_mentioned:
            logger.info(f"Bot {bot.name} was mentioned in message {message_id} (delayed), responding")
        else:
            logger.info(f"Bot {bot.name} was not mentioned in message {message_id} (delayed), but continuing anyway for conversation flow")
        
        # Çoklu mention durumunda sadece bir bot yanıt versin
        mentioned_bots = []
        for channel_bot in ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot'):
            if f"@{channel_bot.bot.name.lower()}" in trigger_content:
                mentioned_bots.append(channel_bot.bot)
        
        if len(mentioned_bots) > 1:
            # Çoklu mention - sadece en küçük ID'li bot yanıt versin
            mentioned_bots.sort(key=lambda b: b.id)
            selected_bot = mentioned_bots[0]
            if selected_bot.id != bot.id:
                logger.info(f"Multiple bots mentioned (delayed), selected {selected_bot.name} (ID: {selected_bot.id}) instead of {bot.name} (ID: {bot.id})")
                # Broadcast that bot finished thinking even when not selected
                async_to_sync(channel_layer.group_send)(
                    f'channel_{channel.id}',
                    {
                        'type': 'bot.finished_thinking',
                        'bot_name': bot.name,
                        'bot_id': bot.id
                    }
                )
                return
            logger.info(f"Bot {bot.name} (ID: {bot.id}) was selected from multiple mentions (delayed)")
        else:
            logger.info(f"Bot {bot.name} was mentioned in message {message_id} (delayed), responding")
        
        # Duplicate check kaldırıldı - botlar sürekli konuşsun

        # Don't respond to own messages
        if trigger_message.author_type == 'bot' and trigger_message.author_bot == bot:
            logger.info(f"Bot {bot.name} skipping delayed response to own message {message_id}")
            # Broadcast that bot finished thinking even when skipping own message
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return

        # Check if channel is still active
        if not channel.is_active:
            logger.info(f"Channel {channel.name} is not active, skipping bot response")
            # Broadcast that bot finished thinking even when channel is inactive
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return

        # Get recent messages for context with different strategies for each bot
        # Bot 1 (John): Focus on last 5 messages for creativity
        # Bot 2 (Mary): Focus on last 8 messages for analysis
        if bot.id == 1:  # John - Creative bot
            recent_messages = Message.objects.filter(channel=channel).order_by('-created_at')[:5]
        else:  # Mary - Analytical bot
            recent_messages = Message.objects.filter(channel=channel).order_by('-created_at')[:8]
        
        llm_messages = [
            {"role": "assistant" if msg.author_type == 'bot' else "user", "content": msg.content_md}
            for msg in reversed(recent_messages)
        ]

        # Delay kaldırıldı - instant chat deneyimi için
        
        # Generate bot response with enhanced context
        enhanced_system_prompt = bot.system_prompt
        enhanced_system_prompt += f"\n\nŞu anda '{channel.name}' kanalındasın. Diğer botlar ve kullanıcılarla doğal bir şekilde konuş. Gerekirse @mention kullanabilirsin ama zorunlu değil."
        
        bot_response_content = router.call_llm(
            provider=bot.llm_provider,
            model=bot.llm_model,
            system_prompt=enhanced_system_prompt,
            messages=llm_messages,
            temperature=bot.temperature,
        )

        if not bot_response_content or "Error:" in bot_response_content:
            logger.error(f"Failed to get a valid response from bot {bot.name} for message {message_id}.")
            # Broadcast that bot finished thinking even when failed
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'bot.finished_thinking',
                    'bot_name': bot.name,
                    'bot_id': bot.id
                }
            )
            return

        # Kendini mention etmişse temizle
        bot_response_content = bot_response_content.replace(f"@{bot.name}", "").replace(f"@{bot.name.lower()}", "").replace(f"@{bot.name.upper()}", "")

        # Save and broadcast bot's response
        bot_message = Message.objects.create(
            channel=channel,
            author_type='bot',
            author_bot=bot,
            content_md=bot_response_content,
        )
        logger.info(f"Bot {bot.name} responded to message {message_id} (delayed).")

        # Broadcast the new message
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(bot_message).data
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {'type': 'message.new', 'message': message_data}
        )

        # Broadcast that bot finished thinking
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bot.finished_thinking',
                'bot_name': bot.name,
                'bot_id': bot.id
            }
        )

        # Bot mesajından sonra diğer botları tetikle (sırayla konuşsunlar)
        # Channel durumunu tekrar kontrol et
        channel.refresh_from_db()
        if channel.is_active:
            # Bot mesajında mention'lanan diğer botları bul
            mentioned_bots = []
            for channel_bot in ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot'):
                if f"@{channel_bot.bot.name.lower()}" in bot_response_content.lower():
                    mentioned_bots.append(channel_bot.bot)
            
            # Mention'lanan bot varsa onu tetikle, yoksa random bot seç
            if mentioned_bots:
                import random
                next_bot = random.choice(mentioned_bots)
                if next_bot != bot:  # Kendini tetikleme
                    bot_response_delayed.apply_async(
                        args=[next_bot.id, bot_message.id],
                        countdown=3  # 3 saniye bekle ki sırayla konuşsunlar
                    )
                    logger.info(f"Triggered {next_bot.name} to respond to {bot.name}'s message (delayed)")
            else:
                # Mention yoksa da random bot seç ki konuşma devam etsin
                import random
                other_bots = list(ChannelBot.objects.filter(
                    channel=channel, 
                    is_active=True
                ).exclude(bot=bot).select_related('bot'))
                
                if other_bots:
                    next_bot = random.choice(other_bots).bot
                    bot_response_delayed.apply_async(
                        args=[next_bot.id, bot_message.id],
                        countdown=3  # 3 saniye bekle ki sırayla konuşsunlar
                    )
                    logger.info(f"Triggered random bot {next_bot.name} to respond to {bot.name}'s message (delayed)")

        return f"Bot {bot.name} responded to message {message_id} (delayed)"

    except Bot.DoesNotExist:
        logger.error(f"Bot with id {bot_id} does not exist.")
    except Message.DoesNotExist:
        logger.error(f"Message with id {message_id} does not exist.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in delayed bot_response for bot {bot_id}, message {message_id}: {e}", exc_info=True)


@shared_task
def refresh_bot_sources(bot_id: int):
    # ... (placeholder)
    pass
