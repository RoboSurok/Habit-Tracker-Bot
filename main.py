import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from data import db_session
from data.__all_models import Habit

main_keyboard = ReplyKeyboardMarkup(
    [["Добавить привычку"],
     ["Отметить выполнение/невыполнение"],
     ["Показать прогресс"],
     ["Удалить привычку"],
     ["Показать список привычек"]],
    resize_keyboard=True)
IMAGE_PATH = "images/image.png"
db_session.global_init("db/habits.db")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка команды /start'''
    # Достаём данные с бд
    user_id = update.message.from_user.id
    session = db_session.create_session()
    try:
        habits = session.query(Habit).filter_by(user_id=user_id).all()
        if habits:
            context.user_data["habits"] = [habit.name for habit in habits]
            context.user_data["progress"] = [[habit.name, habit.is_done] for habit in habits]
            await update.message.reply_text("Привет! Я нашёл твои привычки:\n" + '\n'.join(context.user_data["habits"]) + "\nВыберите действие", reply_markup=main_keyboard)
        else:
            context.user_data["habits"] = []
            context.user_data["progress"] = []
            await update.message.reply_text("Привет! Я бот для отслеживания привычек. Выберите действие:", reply_markup=main_keyboard)
    finally:
        session.close()


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка команды /stop'''
    # Удаляем старые данные и добавляем новые
    user_id = update.message.from_user.id
    session = db_session.create_session()
    try:
        session.query(Habit).filter_by(user_id=user_id).delete()
        for habit, is_done in context.user_data.get("progress", []):
            session.add(Habit(user_id=user_id, name=habit, is_done=is_done))
        session.commit()

        context.user_data.clear()
        context.chat_data.clear()

        await update.message.reply_text("Сессия завершена. До свидания! Чтобы начать заново, напишите /start", reply_markup=ReplyKeyboardRemove())
    finally:
        session.close()


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка команды /image'''
    await update.message.reply_photo(photo=open(IMAGE_PATH, 'rb'))


async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка команды /help'''
    await update.message.reply_text(
        """Привет! Я бот для отслеживания привычек. У меня есть следующие функции:
1. Я могу добавить привычку в список, в котором будут находиться все ваши привычки.
2. Я могу отметить выполнение/невыполнение привычки. Для этого вам нужно выбрать привычку из списка.
3. Я могу показать прогресс выполнения ваших привычек, которые вы добавили.
4. Я могу удалить привычку из списка.
5. Я могу показать список ваших привычек.
Если вы хотите завершить сессию, напишите /stop
Если вы хотите начать, то напишите /start
Чтобы выбрать действие надо выбрать соответствующую кнопку
Также вы можете отправить картинку, а после я буду отправлять её вам в ответ при команде, данная картинка может давать мотивацию, скорее всего... /image"""
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка картинки'''
    try:
        if os.path.exists(IMAGE_PATH):
            os.remove(IMAGE_PATH)
        image_file = await update.message.photo[-1].get_file()
        await image_file.download_to_drive(IMAGE_PATH)
        await update.message.reply_text("Новая картинка успешно сохранена, старая удалена!")
    except:
        await update.message.reply_text("Произошла ошибка при сохранении картинки")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обработка сообщений от пользователя'''
    text = update.message.text
    state = context.user_data.get("state")
    lst_habits = context.user_data.get("habits", [])
    lst_habits_with_progress = context.user_data.get("progress", [])

    if state == "adding_habit":
        if text in lst_habits:
            await update.message.reply_text("Такая привычка уже есть в списке")
        else:
            lst_habits.append(text)
            lst_habits_with_progress.append([text, False])
            await update.message.reply_text("Привычка добавлена. Поздравляем вас с новой привычкой!\n(надеюсь с хорошей))", reply_markup=main_keyboard)
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
                lst_habits_with_progress[choice - 1][1] = not lst_habits_with_progress[choice - 1][1]
                await update.message.reply_text('Статус привычки изменён', reply_markup=main_keyboard)
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
                await update.message.reply_text("Удаление привычки отменено", reply_markup=main_keyboard)
            else:
                del lst_habits[choice - 1]
                del lst_habits_with_progress[choice - 1]
                await update.message.reply_text("Жаль, что вы удалили привычку, но мы помним об этом...", reply_markup=main_keyboard)
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
            await update.message.reply_text("\n".join([f"{i+1}. Привычка: {name}" for i, name in enumerate(lst_habits)]))
            await update.message.reply_text("Если вы не хотите выбирать, введите 0")
            context.user_data["state"] = "mark_done"
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку")

    elif text == "Показать прогресс":
        if lst_habits_with_progress:
            await update.message.reply_text("Прогресс привычек:")
            await update.message.reply_text("\n".join([f"Привычка: {name} " + ("выполнена! :)" if done else "не выполнена... :()") for name, done in lst_habits_with_progress]))
            cnt_done = sum(1 for _, done in lst_habits_with_progress if done)
            await update.message.reply_text("Поздравляем! Все привычки выполнены" if cnt_done == len(lst_habits_with_progress) else f"Выполнено {cnt_done} из {len(lst_habits_with_progress)} привычек, поэтому давайте немного поднапряжёмся.")
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)

    elif text == "Удалить привычку":
        if lst_habits:
            await update.message.reply_text("Выберите привычку (введите номер):")
            await update.message.reply_text("\n".join([f"{i+1}. Привычка: {name}" for i, name in enumerate(lst_habits)]))
            await update.message.reply_text("Если вы не хотите выбирать, введите 0")
            context.user_data["state"] = "delete_habit"
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)

    elif text == "Показать список привычек":
        if lst_habits:
            await update.message.reply_text("Список привычек:")
            await update.message.reply_text("\n".join(lst_habits))
        else:
            await update.message.reply_text("Список привычек пуст, добавьте привычку", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Я не понимаю этот запрос. Пожалуйста, выберите команду с клавиатуры.")

    context.user_data["habits"] = lst_habits
    context.user_data["progress"] = lst_habits_with_progress


def main():
    '''Основная функция запуска бота'''
    token = input()
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_message))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.run_polling()


if __name__ == '__main__':
    main()
