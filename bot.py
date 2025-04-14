import logging
import re
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

CHOOSING, EVENT_NAME, EVENT_DATE, EVENT_START, EVENT_END, EVENT_PEOPLE, EVENT_COLOR, CONFIRM = range(8)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# /start o "ciao"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["📅 New Outlook Event"]]
    await update.message.reply_text(
        "Ciao! Cosa vuoi fare?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING

# scelta
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
    date_text = update.message.text
    try:
        datetime.strptime(date_text, "%d/%m/%Y")
        context.user_data["date"] = date_text
        await update.message.reply_text("Orario di inizio? (formato: HH:MM)")
        return EVENT_START
    except ValueError:
        await update.message.reply_text("⚠️ Formato data non valido. Usa GG/MM/AAAA.")
        return EVENT_DATE

async def get_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_text = update.message.text
    if re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", time_text):
        context.user_data["start"] = time_text
        await update.message.reply_text("Orario di fine? (formato: HH:MM)")
        return EVENT_END
    else:
        await update.message.reply_text("⚠️ Orario non valido. Usa HH:MM.")
        return EVENT_START

async def get_event_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_text = update.message.text
    if re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", time_text):
        context.user_data["end"] = time_text

        # Inline buttons per "Nessuno" o testo
        keyboard = [[InlineKeyboardButton("Nessuno", callback_data="nessuno")]]
        await update.message.reply_text(
            "Chi vuoi invitare? Scrivi una o più email separate da virgola, oppure clicca su 'Nessuno'.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EVENT_PEOPLE
    else:
        await update.message.reply_text("⚠️ Orario non valido. Usa HH:MM.")
        return EVENT_END

async def get_event_people(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    emails = update.message.text
    if emails.strip().lower() == "nessuno":
        context.user_data["people"] = "Nessuno"
    else:
        # semplice validazione base
        email_list = [e.strip() for e in emails.split(",")]
        if all(re.match(r"[^@]+@[^@]+\.[^@]+", e) for e in email_list):
            context.user_data["people"] = ", ".join(email_list)
        else:
            await update.message.reply_text("⚠️ Inserisci email valide, separate da virgole, oppure scrivi 'Nessuno'.")
            return EVENT_PEOPLE

    await update.message.reply_text("Categoria? (scrivila pure, nella fase 2 ti proporremo l’elenco da Outlook)")
    return EVENT_COLOR

# Gestione del bottone "Nessuno"
async def people_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["people"] = "Nessuno"
    await query.edit_message_text("Invitati: Nessuno")
    await query.message.reply_text("Categoria? (scrivila pure, nella fase 2 ti proporremo l’elenco da Outlook)")
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
    await update.message.reply_text("✅ OK, evento creato!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operazione annullata.")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & filters.Regex("(?i)^ciao$"), start)
        ],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            EVENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_name)],
            EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_date)],
            EVENT_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_start)],
            EVENT_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_end)],
            EVENT_PEOPLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_people),
                CallbackQueryHandler(people_button_handler)
            ],
            EVENT_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_color)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
