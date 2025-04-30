from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

main_keyboard = ReplyKeyboardMarkup(
    [["Добавить привычку"],
     ["Отметить выполненное"],
     ["Показать прогресс"],
     ["Удалить привычку"],
     ["Показать список привычек"],
     ["Помощь"]],
    resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для отслеживания привычек. Выберите действие:",
        reply_markup=main_keyboard)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    pass


def main():
    token = input()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == '__main__':
    main()
