from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from models import Session, Habit

main_keyboard = ReplyKeyboardMarkup(
    [["Добавить привычку"],
     ["Отметить выполнение/невыполнение"],
     ["Показать прогресс"],
     ["Удалить привычку"],
     ["Показать список привычек"]],
    resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Достаём данные с бд
    user_id = update.message.from_user.id
    session = Session()
    habits = session.query(Habit).filter_by(user_id=user_id).all()
    global lst_habits
    global lst_habits_with_progress
    if habits:
        lst_habits = [habit.name for habit in habits]
        lst_habits_with_progress = [[habit.name, habit.is_done] for habit in habits]
        await update.message.reply_text(
            "Привет! Я нашёл твои привычки:\n" + "\n".join(lst_habits) + "Выберите действие:", 
            reply_markup=main_keyboard)
    else:
        lst_habits = []
        lst_habits_with_progress = []
        await update.message.reply_text(
            "Привет! Я бот для отслеживания привычек. Выберите действие:",
            reply_markup=main_keyboard)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #Удаляем старые данные и добавляем новые
    user_id = update.message.from_user.id
    session = Session()
    context.user_data.clear()
    context.chat_data.clear()
    session.query(Habit).filter_by(user_id=user_id).delete()
    for habit, is_done in lst_habits_with_progress:
        session.add(Habit(user_id=user_id, name=habit, is_done=is_done))
    session.commit()
    session.close()
    await update.message.reply_text(
        "Сессия завершена. До свидания! Чтобы начать заново, напишите /start",
        reply_markup=ReplyKeyboardRemove()
    )


async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """Привет! Я бот для отслеживания привычек. У меня есть следующие функции:
1. Я могу добавить привычку в список, в котором будут находиться все ваши привычки.
2. Я могу отметить выполнение/невыполнение привычки. Для этого вам нужно выбрать привычку из списка.
3. Я могу показать прогресс выполнения ваших привычек, которые вы добавили.
4. Я могу удалить привычку из списка.
5. Я могу показать список ваших привычек.
Если вы хотите завершить сессию, напишите /stop
Если вы хотите начать, то напишите /start
Чтобы выбрать действие надо выбрать соответствующую кнопку"""
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Обработка промежуточного ввода
    state = context.user_data.get("state")

    if state == "adding_habit":
        if text in lst_habits:
            await update.message.reply_text("Такая привычка уже есть в списке")
        else:
            lst_habits.append(text)
            lst_habits_with_progress.append([text, False])
            await update.message.reply_text("Привычка добавлена в список", reply_markup=main_keyboard)
        context.user_data["state"] = None
        return

    elif state == "mark_done":
        try:
            choice = int(text)
            if not (0 <= choice <= len(lst_habits)):
                await update.message.reply_text(f"Такого номера не существует, введите число от 0 до {len(lst_habits)}")
            elif choice == 0:
                await update.message.reply_text("Выбор привычки отменен", reply_markup=main_keyboard)
            else:
                lst_habits_with_progress[choice - 1][1] = True if not lst_habits_with_progress[choice - 1][1] else False
                await update.message.reply_text("Привычка выполнена", reply_markup=main_keyboard)
            context.user_data["state"] = None
        except ValueError:
            await update.message.reply_text("Введите корректный номер")
        return

    elif state == "delete_habit":
        try:
            choice = int(text)
            if not (0 <= choice <= len(lst_habits)):
                await update.message.reply_text(f"Такого номера не существует, введите число от 0 до {len(lst_habits)}")
            elif choice == 0:
                await update.message.reply_text("Выбор привычки отменен", reply_markup=main_keyboard)
            else:
                del lst_habits[choice - 1]
                del lst_habits_with_progress[choice - 1]
                await update.message.reply_text("Привычка удалена", reply_markup=main_keyboard)
            context.user_data["state"] = None
        except ValueError:
            await update.message.reply_text("Введите корректный номер")
        return

    # Основное меню — кнопки
    if text == "Добавить привычку":
        await update.message.reply_text("Введите название привычки")
        context.user_data["state"] = "adding_habit"

    elif text == "Отметить выполнение/невыполнение":
        if lst_habits:
            await update.message.reply_text("Выберите привычку (введите номер):")
            await update.message.reply_text("\n".join([f"{i+1}. Привычка: {lst_habits[i]}" for i in range(len(lst_habits))]))
            await update.message.reply_text("Если вы не хотите выбирать, введите 0")
            context.user_data["state"] = "mark_done"
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку")

    elif text == "Показать прогресс":
        if lst_habits_with_progress:
            await update.message.reply_text("Прогресс привычек:")
            await update.message.reply_text("\n".join([f"Привычка: {el[0]} " + ("выполнена! :)" if el[1] else "не выполнена... :()") for el in lst_habits_with_progress]))
            cnt_done = sum([el[1] for el in lst_habits_with_progress])
            await update.message.reply_text("Все привычки выполнены" if cnt_done == len(lst_habits_with_progress) else f"Выполнено {cnt_done} из {len(lst_habits_with_progress)} привычек")
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)

    elif text == "Удалить привычку":
        if lst_habits:
            await update.message.reply_text("Выберите привычку (введите номер):")
            await update.message.reply_text("\n".join([f"{i+1}. Привычка: {lst_habits[i]}" for i in range(len(lst_habits))]))
            await update.message.reply_text("Если вы не хотите выбирать, введите 0")
            context.user_data["state"] = "delete_habit"
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)

    elif text == "Показать список привычек":
        if lst_habits:
            await update.message.reply_text("Список привычек:")
            await update.message.reply_text("\n".join([f"Привычка: {el}" for el in lst_habits]))
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Я не понимаю этот запрос. Пожалуйста, выберите команду с клавиатуры.")



def main():
    token = input()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == '__main__':
    main()

