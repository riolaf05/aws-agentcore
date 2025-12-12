"""
Script per ricevere messaggi testuali dal bot Telegram e inviarli all'Orchestrator Agent.
Può essere eseguito standalone per testing o integrato nel webhook.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
import boto3
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Carica variabili d'ambiente
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS clients
lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ORCHESTRATOR_LAMBDA_ARN = os.getenv('LAMBDA_ORCHESTRATOR_ARN')
AUTHORIZED_CHAT_IDS = os.getenv('TELEGRAM_CHAT_ID', '').split(',')


class TelegramToAgentHandler:
    """
    Handler che inoltra messaggi Telegram all'Orchestrator Agent.
    """
    
    def __init__(self, orchestrator_arn: str):
        self.orchestrator_arn = orchestrator_arn
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Riceve messaggi testuali e li inoltra all'Orchestrator Agent.
        """
        try:
            # Ottieni informazioni sul messaggio
            chat_id = str(update.effective_chat.id)
            user_id = str(update.effective_user.id)
            username = update.effective_user.username or update.effective_user.first_name
            message_text = update.message.text
            
            # Verifica autorizzazione
            if not self._is_authorized(chat_id):
                logger.warning(f"Unauthorized access attempt from chat_id: {chat_id}")
                await update.message.reply_text(
                    "⛔ Non sei autorizzato a usare questo bot.\n"
                    f"Chat ID: `{chat_id}`",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"Received message from {username} (chat_id: {chat_id}): {message_text}")
            
            # Mostra typing indicator
            await update.message.chat.send_action("typing")
            
            # Inoltra all'Orchestrator Agent
            response = await self._invoke_orchestrator_async(
                message=message_text,
                user_id=user_id,
                chat_id=chat_id,
                username=username
            )
            
            # Invia risposta
            if response.get('success'):
                agent_reply = response.get('response', {}).get('message', 'Nessuna risposta dall\'agente.')
                await update.message.reply_text(agent_reply, parse_mode='Markdown')
                logger.info(f"Sent response to {username}")
            else:
                error_msg = response.get('error', 'Errore sconosciuto')
                await update.message.reply_text(
                    f"❌ Errore durante l'elaborazione: {error_msg}"
                )
                logger.error(f"Error from orchestrator: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Si è verificato un errore interno. Riprova più tardi."
            )
    
    async def _invoke_orchestrator_async(
        self, 
        message: str, 
        user_id: str, 
        chat_id: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Invoca l'Orchestrator Agent in modo asincrono.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._invoke_orchestrator, 
            message, 
            user_id, 
            chat_id,
            username
        )
    
    def _invoke_orchestrator(
        self, 
        message: str, 
        user_id: str, 
        chat_id: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Invoca l'Orchestrator Agent tramite Lambda.
        """
        try:
            payload = {
                'body': json.dumps({
                    'message': message,
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'username': username,
                    'source': 'telegram'
                })
            }
            
            logger.info(f"Invoking Orchestrator Lambda: {self.orchestrator_arn}")
            
            response = lambda_client.invoke(
                FunctionName=self.orchestrator_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            
            # Gestisci errori Lambda
            if response.get('FunctionError'):
                return {
                    'success': False,
                    'error': f"Lambda error: {response_payload}"
                }
            
            body = json.loads(response_payload.get('body', '{}'))
            
            return body
            
        except Exception as e:
            logger.error(f"Error invoking orchestrator: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_authorized(self, chat_id: str) -> bool:
        """
        Verifica se la chat è autorizzata.
        """
        if not AUTHORIZED_CHAT_IDS or AUTHORIZED_CHAT_IDS == ['']:
            logger.warning("No chat ID filter configured - accepting all chats")
            return True
        
        is_auth = chat_id in AUTHORIZED_CHAT_IDS
        logger.debug(f"Authorization check for chat_id {chat_id}: {is_auth}")
        return is_auth


async def run_bot():
    """
    Avvia il bot Telegram in modalità polling per ricevere messaggi.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN non configurato nel file .env")
    
    if not ORCHESTRATOR_LAMBDA_ARN:
        raise ValueError("LAMBDA_ORCHESTRATOR_ARN non configurato nel file .env")
    
    logger.info("Starting Telegram bot in polling mode...")
    logger.info(f"Orchestrator ARN: {ORCHESTRATOR_LAMBDA_ARN}")
    logger.info(f"Authorized chat IDs: {AUTHORIZED_CHAT_IDS}")
    
    # Crea application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Crea handler
    handler = TelegramToAgentHandler(ORCHESTRATOR_LAMBDA_ARN)
    
    # Registra handler per messaggi testuali (esclusi comandi)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handler.handle_text_message
        )
    )
    
    logger.info("✅ Bot avviato! Inizia a inviare messaggi...")
    
    # Avvia polling
    await application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


def main():
    """
    Entry point principale.
    """
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot fermato dall'utente")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
