import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Stati della conversazione
CHOOSING, EVENT_NAME, EVENT_DATE, EVENT_START, EVENT_END, EVENT_PEOPLE, EVENT_COLOR, CONFIRM = range(8)

# Abilita il logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Start / ciao
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["📅 New Outlook Event"]]
    await update.message.reply_text(
        "Ciao! Cosa vuoi fare?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING

# Scelta dell'azione
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if "Outlook" in text:
        await update.message.reply_text("Come si chiama l’evento?")
        return EVENT_NAME
    return CHOOSING

async def get_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Che data? (formato: GG/MM/AAAA)")
    return EVENT_DATE

async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["date"] = update.message.text
    await update.message.reply_text("Orario di inizio? (es: 14:00)")
    return EVENT_START

async def get_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["start"] = update.message.text
    await update.message.reply_text("Orario di fine? (es: 15:00)")
    return EVENT_END

async def get_event_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["end"] = update.message.text
    await update.message.reply_text("Chi vuoi invitare? (email separate da virgola)")
    return EVENT_PEOPLE

async def get_event_people(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["people"] = update.message.text
    await update.message.reply_text("Colore/categoria (es: Lavoro, Personale...)")
    return EVENT_COLOR

async def get_event_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["color"] = update.message.text
    summary = (
        f"📝 **Riepilogo Evento**\n"
        f"📌 Nome: {context.user_data['name']}\n"
        f"📅 Data: {context.user_data['date']}\n"
        f"⏰ Orario: {context.user_data['start']} - {context.user_data['end']}\n"
        f"👥 Partecipanti: {context.user_data['people']}\n"
        f"🎨 Categoria: {context.user_data['color']}\n\n"
        f"Premi 'Conferma' per creare l’evento."
    )
    await update.message.reply_text(summary)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("✅ Evento pronto! (in futuro sarà creato su Outlook)")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operazione annullata.")
    return ConversationHandler.END

# Main
def main():
    import os
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & filters.Regex("(?i)^ciao$"), start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_name)],
            EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_date)],
            EVENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_start)],
            EVENT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_end)],
            EVENT_PEOPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_people)],
            EVENT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_color)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
