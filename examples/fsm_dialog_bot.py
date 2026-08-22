"""
Interactive Multi-step Dialog Bot with Finite State Machine (FSM).
"""
from maxlib import MaxClient, filters, Message, State, StatesGroup

client = MaxClient("survey_bot")


class Registration(StatesGroup):
    name = State()
    city = State()
    confirm = State()


@client.on_message(filters.command("register"))
async def start_registration(client: MaxClient, message: Message):
    await client.fsm.set_state(message.chat_id, message.sender_id, Registration.name)
    await message.reply("📝 **Регистрация начата!**\nКак вас зовут?")


@client.on_message(filters.state(Registration.name))
async def process_name(client: MaxClient, message: Message):
    await client.fsm.update_data(message.chat_id, message.sender_id, name=message.text)
    await client.fsm.set_state(message.chat_id, message.sender_id, Registration.city)
    await message.reply(f"Приятно познакомиться, **{message.text}**! В каком городе вы живёте?")


@client.on_message(filters.state(Registration.city))
async def process_city(client: MaxClient, message: Message):
    data = await client.fsm.update_data(message.chat_id, message.sender_id, city=message.text)
    await client.fsm.clear(message.chat_id, message.sender_id)
    await message.reply(
        f"✅ **Регистрация завершена!**\n"
        f"• Имя: `{data.get('name')}`\n"
        f"• Город: `{data.get('city')}`"
    )


if __name__ == "__main__":
    client.run()
