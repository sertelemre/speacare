from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from collab.models import Channel, ChannelMember, ChannelBot
from bots.models import Bot

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create a superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create a regular user
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created demo user'))
        
        # Create channels
        channels_data = [
            {
                'name': '🚀 Ürün Lansman',
                'description': 'Yeni ürün lansmanı için tartışmalar',
                'is_private': False
            },
            {
                'name': '📈 Fiyatlandırma',
                'description': 'Fiyatlandırma stratejileri ve analizler',
                'is_private': False
            },
            {
                'name': '🧪 Deneyler',
                'description': 'A/B testleri ve deney tasarımları',
                'is_private': False
            }
        ]
        
        for channel_data in channels_data:
            channel, created = Channel.objects.get_or_create(
                name=channel_data['name'],
                defaults={
                    'description': channel_data['description'],
                    'is_private': channel_data['is_private'],
                    'created_by': user
                }
            )
            if created:
                # Add user as member
                ChannelMember.objects.create(
                    channel=channel,
                    user=user,
                    role='owner'
                )
                self.stdout.write(self.style.SUCCESS(f'Created channel: {channel.name}'))
        
        # Create bots
        bots_data = [
            {
                'name': 'CMO',
                'title': 'Chief Marketing Officer',
                'persona_json': {
                    'role': 'Marketing strategist',
                    'expertise': ['brand positioning', 'market analysis', 'customer acquisition'],
                    'style': 'Data-driven and customer-focused'
                },
                'llm_provider': 'groq',
                'llm_model': 'llama3-8b-8192',
                'temperature': 0.9,
                'system_prompt': 'You are a Chief Marketing Officer with expertise in brand positioning and market analysis.',
                'background': 'Experienced marketing executive with 15+ years in tech startups.',
                'expertise_tags': ['marketing', 'branding', 'analytics'],
                'stance_profile': 'support'
            },
            {
                'name': 'Satış Direktörü',
                'title': 'Sales Director',
                'persona_json': {
                    'role': 'Sales strategist',
                    'expertise': ['revenue growth', 'sales processes', 'customer relationships'],
                    'style': 'Results-oriented and relationship-focused'
                },
                'llm_provider': 'openai',
                'llm_model': 'gpt-4o',
                'temperature': 0.6,
                'system_prompt': 'You are a Sales Director focused on revenue growth and customer relationships.',
                'background': 'Proven sales leader with track record of scaling sales teams.',
                'expertise_tags': ['sales', 'revenue', 'processes'],
                'stance_profile': 'support'
            },
            {
                'name': 'Finans Analisti',
                'title': 'Financial Analyst',
                'persona_json': {
                    'role': 'Financial strategist',
                    'expertise': ['financial modeling', 'cost analysis', 'ROI calculations'],
                    'style': 'Analytical and risk-aware'
                },
                'llm_provider': 'gemini',
                'llm_model': 'gemini-1.5-pro-latest',
                'temperature': 0.5,
                'system_prompt': 'You are a Financial Analyst focused on cost-benefit analysis and ROI.',
                'background': 'CFA with expertise in startup financial modeling.',
                'expertise_tags': ['finance', 'analytics', 'modeling'],
                'stance_profile': 'critical'
            },
            {
                'name': 'PM',
                'title': 'Product Manager',
                'persona_json': {
                    'role': 'Product strategist',
                    'expertise': ['product roadmap', 'user research', 'feature prioritization'],
                    'style': 'User-centric and strategic'
                },
                'llm_provider': 'gemini',
                'llm_model': 'gemini-1.5-pro-latest',
                'temperature': 0.8,
                'system_prompt': 'You are a Product Manager focused on user needs and product strategy.',
                'background': 'Product leader with experience in B2B SaaS products.',
                'expertise_tags': ['product', 'strategy', 'user-research'],
                'stance_profile': 'neutral'
            },
            {
                'name': 'Devil\'s Advocate',
                'title': 'Devil\'s Advocate',
                'persona_json': {
                    'role': 'Critical challenger',
                    'expertise': ['risk identification', 'assumption testing', 'alternative perspectives'],
                    'style': 'Skeptical and challenging'
                },
                'llm_provider': 'groq',
                'llm_model': 'llama3-8b-8192',
                'temperature': 0.8,
                'system_prompt': 'You are a Devil\'s Advocate who challenges ideas to find weaknesses and risks.',
                'background': 'Strategic consultant with expertise in risk analysis.',
                'expertise_tags': ['risk', 'challenge', 'analysis'],
                'stance_profile': 'devils_advocate'
            },
            {
                'name': 'Risk Analisti',
                'title': 'Risk Analyst',
                'persona_json': {
                    'role': 'Risk assessment specialist',
                    'expertise': ['risk modeling', 'scenario analysis', 'mitigation strategies'],
                    'style': 'Methodical and thorough'
                },
                'llm_provider': 'deepseek',
                'llm_model': 'deepseek-chat',
                'temperature': 0.4,
                'system_prompt': 'You are a Risk Analyst who identifies and quantifies potential risks.',
                'background': 'Risk management expert with experience in financial and operational risks.',
                'expertise_tags': ['risk', 'modeling', 'mitigation'],
                'stance_profile': 'critical'
            },
            {
                'name': 'Scribe',
                'title': 'Scribe',
                'persona_json': {
                    'role': 'Meeting facilitator and note-taker',
                    'expertise': ['summarization', 'decision tracking', 'action items'],
                    'style': 'Neutral and organized'
                },
                'llm_provider': 'gemini',
                'llm_model': 'gemini-1.5-flash',
                'temperature': 0.3,
                'system_prompt': 'You are a Scribe who summarizes discussions and tracks decisions.',
                'background': 'Professional meeting facilitator with expertise in documentation.',
                'expertise_tags': ['documentation', 'summarization', 'facilitation'],
                'stance_profile': 'neutral'
            },
            {
                'name': 'Doc-Maker',
                'title': 'Document Maker',
                'persona_json': {
                    'role': 'Document creator',
                    'expertise': ['consensus building', 'documentation', 'stakeholder alignment'],
                    'style': 'Collaborative and clear'
                },
                'llm_provider': 'openai',
                'llm_model': 'gpt-4o',
                'temperature': 0.5,
                'system_prompt': 'You are a Document Maker who creates consensus documents and briefs.',
                'background': 'Technical writer with experience in stakeholder alignment.',
                'expertise_tags': ['documentation', 'consensus', 'alignment'],
                'stance_profile': 'neutral'
            }
        ]
        
        for bot_data in bots_data:
            bot, created = Bot.objects.get_or_create(
                name=bot_data['name'],
                defaults={
                    **bot_data,
                    'created_by': user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created bot: {bot.name}'))
        
        # Add bots to channels
        channels = Channel.objects.all()
        bots = Bot.objects.all()
        
        for channel in channels:
            for bot in bots:
                channel_bot, created = ChannelBot.objects.get_or_create(
                    channel=channel,
                    bot=bot,
                    defaults={
                        'is_active': True,
                        'join_policy': 'always'
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Added {bot.name} to {channel.name}'))
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
