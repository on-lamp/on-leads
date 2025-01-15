import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.functions.crawl_contacts import crawl_and_store_contacts
from src.functions.draft_message import draft_first_contact, draft_all_first_contacts
from src.integrations.notion import NotionIntegration
from src.types.database import DatabaseType, LeadRecord, EmailRecord

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Update commands dictionary
COMMANDS = {
    'start': 'Start OnLeads AI agent and show welcome message',
    'help': 'Show this help message',
    'crawl': 'Extract email contacts from a webpage and store them in Notion CRM. Usage: /crawl <url>',
    'draft': 'Draft first contact email for a specific lead. Usage: /draft <lead_id> <prompt>',
    'draft_all': 'Draft first contact emails for all leads. Usage: /draft_all <prompt>'
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = "Available commands:\n\n"
    for command, description in COMMANDS.items():
        help_text += f"/{command} - {description}\n"
    await update.message.reply_text(help_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Hello! I am OnLeads, your AI agent for CRM management.\n'
        'I can help you gather and manage contacts in your Notion database.\n'
        'Use /help to see the list of available commands.'
    )

async def crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_text('Please provide the webpage URL. Usage: /crawl <url>')
        return

    url = context.args[0]
    await update.message.reply_text(
        f'Starting to analyze {url}\n'
        'I will scan the webpage for email contacts and add them to your Notion CRM.'
    )

    # Initialize database clients
    leads_db = NotionIntegration[LeadRecord](DatabaseType.LEADS)
    await leads_db.connect()
    
    try:
        result = await crawl_and_store_contacts(url=url, leads_db=leads_db)
        await update.message.reply_text(
            'Email extraction completed successfully!\n'
            'All found contacts have been added to your Notion CRM.'
        )
    except Exception as e:
        await update.message.reply_text(f'Error while extracting email contacts: {str(e)}')

async def draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text('Please provide lead ID and prompt. Usage: /draft <lead_id> <prompt>')
        return

    try:
        lead_id = int(context.args[0])  # Convert lead_id to integer
        user_prmpt = ' '.join(context.args[1:])
    except ValueError:
        await update.message.reply_text('Lead ID must be a number')
        return
    
    # Initialize database clients
    leads_db = NotionIntegration[LeadRecord](DatabaseType.LEADS)
    emails_db = NotionIntegration[EmailRecord](DatabaseType.EMAILS)
    await leads_db.connect()
    await emails_db.connect()
    
    try:
        await update.message.reply_text(f'Drafting first contact email for lead {lead_id}...')
        email = await draft_first_contact(
            lead_id=lead_id,
            user_prmpt=user_prmpt,
            leads_db=leads_db,
            emails_db=emails_db
        )
        
        if email:
            await update.message.reply_text(
                f'Email drafted successfully!\n\n'
                f'Subject: {email.object}\n\n'
                f'Body:\n{email.body}'
            )
        else:
            await update.message.reply_text('First contact email already exists for this lead.')
    except Exception as e:
        await update.message.reply_text(f'Error while drafting email: {str(e)}')

async def draft_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Please provide a prompt. Usage: /draft_all <prompt>')
        return

    prompt = ' '.join(context.args)
    
    # Initialize database clients
    leads_db = NotionIntegration[LeadRecord](DatabaseType.LEADS)
    emails_db = NotionIntegration[EmailRecord](DatabaseType.EMAILS)
    await leads_db.connect()
    await emails_db.connect()
    
    try:
        await update.message.reply_text('Starting to draft first contact emails for all leads...')
        emails = await draft_all_first_contacts(
            leads_db=leads_db,
            emails_db=emails_db,
            user_prmpt=prompt
        )
        
        await update.message.reply_text(
            f'Successfully drafted {len(emails)} new first contact emails.\n'
            'Check your Notion database for the results.'
        )
    except Exception as e:
        await update.message.reply_text(f'Error while drafting emails: {str(e)}')

async def set_commands(application: Application):
    """Set bot commands in Telegram"""
    await application.bot.set_my_commands([
        (command, description) for command, description in COMMANDS.items()
    ])

def main():
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("crawl", crawl))
    application.add_handler(CommandHandler("draft", draft))
    application.add_handler(CommandHandler("draft_all", draft_all))

    # Set up commands for suggestions
    if application.job_queue:
        application.job_queue.run_once(set_commands, 1)

    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
