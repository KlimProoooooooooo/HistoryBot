import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = ""
# Вставьте сюда ID вашей группы (начинается с минуса, например: -1001234567890)
ADMIN_ID = 

bot = Bot(token=TOKEN)
dp = Dispatcher()


class StudentForm(StatesGroup):
  waiting_for_name = State()
  waiting_for_group = State()
  waiting_for_work = State()


class TeacherCommentForm(StatesGroup):
  waiting_for_comment = State()


# Команда /start (теперь только с текстом и кнопкой)
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
  builder = InlineKeyboardBuilder()
  builder.button(
      text="📝 Сдать работу по истории", callback_data="start_submission"
  )

  text = (
      "🇷🇺 **ИСТОРИЯ РОССИИ**\n\n"
      "👋 Здравствуйте!\n"
      "Этот бот предназначен для сдачи и проверки проверочных работ.\n\n"
      "Нажмите на кнопку ниже, чтобы отправить задание:"
  )

  await message.answer(
      text, parse_mode="Markdown", reply_markup=builder.as_markup()
  )


@dp.callback_query(F.data == "start_submission")
async def process_callback_start(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "📌 **Шаг 1 из 3**\n\nВведите ваши **Фамилию, Имя и Отчество** (например,"
      " *Иванов Иван Иванович*):",
      parse_mode="Markdown",
  )
  await state.set_state(StudentForm.waiting_for_name)
  await callback.answer()


@dp.message(StudentForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
  await state.update_data(student_name=message.text)
  await message.answer(
      f"✅ Приятно познакомиться, **{message.text}**!\n\n"
      "📌 **Шаг 2 из 3**\n"
      "Укажите вашу **группу** (например, *ИСТ-21*):",
      parse_mode="Markdown",
  )
  await state.set_state(StudentForm.waiting_for_group)


@dp.message(StudentForm.waiting_for_group)
async def process_group(message: types.Message, state: FSMContext):
  await state.update_data(student_group=message.text)
  await message.answer(
      "✅ Группа записана!\n\n"
      "📌 **Шаг 3 из 3**\n"
      "Отправьте файл с вашей работой (**Word**, **PDF** или текст):",
      parse_mode="Markdown",
  )
  await state.set_state(StudentForm.waiting_for_work)


@dp.message(StudentForm.waiting_for_work)
async def process_work(message: types.Message, state: FSMContext):
  data = await state.get_data()
  name = data.get("student_name")
  group = data.get("student_group")
  student_id = message.from_user.id

  await message.answer(
      f"🎉 **Готово, {name}!**\n\n"
      f"Ваша работа (группа: *{group}*) отправлена преподавателю на"
      " проверку. 📚",
      parse_mode="Markdown",
  )

  builder = InlineKeyboardBuilder()
  builder.button(text="✅ Зачесть", callback_data=f"pass_{student_id}")
  builder.button(text="❌ На доработку", callback_data=f"fail_{student_id}")
  builder.button(
      text="💬 Написать комментарий", callback_data=f"comment_{student_id}"
  )
  builder.adjust(2, 1)

  report_text = (
      f"📥 **Новая работа на проверку!**\n\n"
      f"👤 **Студент:** {name}\n"
      f"🎓 **Группа:** {group}"
  )

  await bot.send_message(
      chat_id=ADMIN_ID,
      text=report_text,
      parse_mode="Markdown",
      reply_markup=builder.as_markup(),
  )
  await message.forward(chat_id=ADMIN_ID)

  await state.clear()


@dp.callback_query(F.data.startswith("pass_"))
async def grade_pass(callback: types.CallbackQuery):
  student_id = int(callback.data.split("_")[1])

  await bot.send_message(
      chat_id=student_id,
      text=(
          "🎉 **Ваша работа по истории успешно проверена и зачтена!** Отличная"
          " работа! 🏆"
      ),
      parse_mode="Markdown",
  )

  await callback.message.edit_text(
      f"{callback.message.text}\n\nstatus: **✅ ЗАЧТЕНО**", parse_mode="Markdown"
  )
  await callback.answer("Работа принята!")


@dp.callback_query(F.data.startswith("fail_"))
async def grade_fail(callback: types.CallbackQuery):
  student_id = int(callback.data.split("_")[1])

  await bot.send_message(
      chat_id=student_id,
      text=(
          "⚠️ **Ваша работа по истории отправлена на доработку.** Пожалуйста,"
          " учтите замечания преподавателя и отправьте файл повторно."
      ),
      parse_mode="Markdown",
  )

  await callback.message.edit_text(
      f"{callback.message.text}\n\nstatus: **❌ НА ДОРАБОТКУ**",
      parse_mode="Markdown",
  )
  await callback.answer("Работа отправлена на доработку.")


@dp.callback_query(F.data.startswith("comment_"))
async def start_comment(callback: types.CallbackQuery, state: FSMContext):
  student_id = int(callback.data.split("_")[1])
  await state.update_data(target_student_id=student_id)

  await callback.message.answer(
      "💬 Введите текст комментария/замечания для этого студента:"
  )
  await state.set_state(TeacherCommentForm.waiting_for_comment)
  await callback.answer()


@dp.message(TeacherCommentForm.waiting_for_comment)
async def send_teacher_comment(message: types.Message, state: FSMContext):
  data = await state.get_data()
  student_id = data.get("target_student_id")
  comment_text = message.text

  await bot.send_message(
      chat_id=student_id,
      text=f"📌 **Комментарий преподавателя к вашей работе:**\n\n{comment_text}",
      parse_mode="Markdown",
  )

  await message.answer("✅ Комментарий успешно отправлен студенту!")
  await state.clear()


async def main():
  logging.basicConfig(level=logging.INFO)
  print("Бот успешно запущен!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
