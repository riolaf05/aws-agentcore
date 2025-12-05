"""
Telegram Bot per comunicare con la suite di agenti AWS.
Gestisce webhook e inoltra messaggi all'Orchestrator Agent.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
import boto3
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ORCHESTRATOR_LAMBDA_ARN = os.environ.get('LAMBDA_ORCHESTRATOR_ARN')
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS', '').split(',')


class TelegramBotHandler:
    """
    Handler per il bot Telegram che comunica con gli agenti AWS.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce messaggi generici dall'utente.
        """
        try:
            user_id = str(update.effective_user.id)
            message_text = update.message.text
            
            # Verifica autorizzazione
            if not self._is_authorized(user_id):
                await update.message.reply_text(
                    "⛔ Non sei autorizzato a usare questo bot."
                )
                return
            
            logger.info(f"Message from user {user_id}: {message_text}")
            
            # Mostra typing indicator
            await update.message.chat.send_action("typing")
            
            # Inoltra all'Orchestrator Agent
            response = self._invoke_orchestrator(message_text, user_id)
            
            # Invia risposta
            if response.get('success'):
                reply = response.get('response', {}).get('message', 'Nessuna risposta.')
                await update.message.reply_text(reply, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ Errore: {response.get('message', 'Errore sconosciuto')}"
                )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Si è verificato un errore. Riprova più tardi."
            )
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce comando /start.
        """
        user_id = str(update.effective_user.id)
        
        if not self._is_authorized(user_id):
            await update.message.reply_text(
                "⛔ Non sei autorizzato a usare questo bot.\n"
                f"Il tuo user ID è: `{user_id}`",
                parse_mode='Markdown'
            )
            return
        
        welcome_message = (
            "👋 **Benvenuto nel tuo Assistente Personale AI!**\n\n"
            "Posso aiutarti a:\n"
            "• 📝 Creare task da obiettivi\n"
            "• 📊 Generare briefing giornalieri\n"
            "• 📋 Gestire i tuoi impegni\n\n"
            "**Comandi disponibili:**\n"
            "/briefing - Riassunto impegni\n"
            "/tasks - Lista task\n"
            "/add <obiettivo> - Aggiungi task\n"
            "/help - Mostra aiuto\n\n"
            "Oppure scrivi semplicemente cosa vuoi fare!"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def handle_briefing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce comando /briefing per riassunto giornaliero.
        """
        try:
            user_id = str(update.effective_user.id)
            
            if not self._is_authorized(user_id):
                await update.message.reply_text("⛔ Non autorizzato")
                return
            
            await update.message.chat.send_action("typing")
            
            # Inoltra richiesta briefing
            response = self._invoke_orchestrator("/briefing", user_id)
            
            if response.get('success'):
                briefing = response.get('response', {}).get('message', 'Nessun briefing')
                await update.message.reply_text(briefing, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Errore nel generare briefing")
            
        except Exception as e:
            logger.error(f"Error in briefing command: {e}")
            await update.message.reply_text("❌ Errore")
    
    async def handle_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce comando /tasks per lista task.
        """
        try:
            user_id = str(update.effective_user.id)
            
            if not self._is_authorized(user_id):
                await update.message.reply_text("⛔ Non autorizzato")
                return
            
            await update.message.chat.send_action("typing")
            
            response = self._invoke_orchestrator("/tasks", user_id)
            
            if response.get('success'):
                message = response.get('response', {}).get('message', 'Nessun task')
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Errore nel recuperare task")
            
        except Exception as e:
            logger.error(f"Error in tasks command: {e}")
            await update.message.reply_text("❌ Errore")
    
    async def handle_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce comando /add <obiettivo> per creare task.
        """
        try:
            user_id = str(update.effective_user.id)
            
            if not self._is_authorized(user_id):
                await update.message.reply_text("⛔ Non autorizzato")
                return
            
            # Estrai obiettivo dal comando
            objective = ' '.join(context.args) if context.args else None
            
            if not objective:
                await update.message.reply_text(
                    "⚠️ Uso: /add <obiettivo>\n"
                    "Esempio: /add Imparare Python entro 3 mesi"
                )
                return
            
            await update.message.chat.send_action("typing")
            
            response = self._invoke_orchestrator(objective, user_id)
            
            if response.get('success'):
                message = response.get('response', {}).get('message', 'Task creati!')
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Errore nel creare task")
            
        except Exception as e:
            logger.error(f"Error in add command: {e}")
            await update.message.reply_text("❌ Errore")
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Gestisce comando /help.
        """
        help_message = (
            "🤖 **Aiuto - Assistente Personale AI**\n\n"
            "**Comandi:**\n"
            "• `/start` - Messaggio di benvenuto\n"
            "• `/briefing` - Riassunto giornaliero con task ed email\n"
            "• `/tasks` - Lista di tutti i task\n"
            "• `/add <obiettivo>` - Crea task da un obiettivo\n"
            "• `/help` - Mostra questo messaggio\n\n"
            "**Esempi di utilizzo:**\n"
            "```\n"
            "/add Imparare Python entro 3 mesi\n"
            "Voglio sviluppare un'app mobile\n"
            "Mostrami i task urgenti\n"
            "```\n\n"
            "Puoi anche scrivere in linguaggio naturale!"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    def _invoke_orchestrator(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Invoca l'Orchestrator Agent tramite Lambda.
        """
        try:
            payload = {
                'body': json.dumps({
                    'message': message,
                    'user_id': user_id
                })
            }
            
            response = lambda_client.invoke(
                FunctionName=ORCHESTRATOR_LAMBDA_ARN,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            body = json.loads(response_payload.get('body', '{}'))
            
            return body
            
        except Exception as e:
            logger.error(f"Error invoking orchestrator: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_authorized(self, user_id: str) -> bool:
        """
        Verifica se l'utente è autorizzato.
        """
        if not AUTHORIZED_USERS or AUTHORIZED_USERS == ['']:
            return True  # Nessun filtro
        
        return user_id in AUTHORIZED_USERS


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler per webhook Telegram.
    Riceve update da Telegram e li processa.
    """
    try:
        # Parse Telegram update
        body = json.loads(event.get('body', '{}'))
        
        # Create bot application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        bot_handler = TelegramBotHandler(TELEGRAM_BOT_TOKEN)
        
        # Register handlers
        application.add_handler(CommandHandler("start", bot_handler.handle_start))
        application.add_handler(CommandHandler("briefing", bot_handler.handle_briefing))
        application.add_handler(CommandHandler("tasks", bot_handler.handle_tasks))
        application.add_handler(CommandHandler("add", bot_handler.handle_add))
        application.add_handler(CommandHandler("help", bot_handler.handle_help))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_message))
        
        # Process update
        update = Update.de_json(body, application.bot)
        
        # Run handler asynchronously
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            application.process_update(update)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Per testing locale con polling
if __name__ == "__main__":
    import asyncio
    from telegram.ext import Application
    
    async def main():
        """Run bot in polling mode for local testing."""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        bot_handler = TelegramBotHandler(TELEGRAM_BOT_TOKEN)
        
        # Register handlers
        application.add_handler(CommandHandler("start", bot_handler.handle_start))
        application.add_handler(CommandHandler("briefing", bot_handler.handle_briefing))
        application.add_handler(CommandHandler("tasks", bot_handler.handle_tasks))
        application.add_handler(CommandHandler("add", bot_handler.handle_add))
        application.add_handler(CommandHandler("help", bot_handler.handle_help))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handler.handle_message))
        
        print("🤖 Bot started in polling mode...")
        await application.run_polling()
    
    asyncio.run(main())
