# Finite State Machine (FSM)

The Finite State Machine (FSM) allows constructing multi-step conversation flows, forms, surveys, and interactive wizards.

---

## 1. Defining States

States are declared inside a class inheriting from `StatesGroup`:

```python
from maxlib import State, StatesGroup


class UserSurvey(StatesGroup):
    name = State()       # Step 1: user enters name
    age = State()        # Step 2: user enters age
    city = State()       # Step 3: user enters city
    confirm = State()    # Step 4: confirmation
```

---

## 2. Implementing the Dialog Flow

```python
from maxlib import MaxClient, filters, Message

client = MaxClient("survey_bot")


# 1. Start survey command
@client.on_message(filters.command("survey"))
async def start_survey(client: MaxClient, message: Message):
    # Transition user to the first state
    await client.fsm.set_state(message.chat_id, message.sender_id, UserSurvey.name)
    await message.reply("Hello! Let's fill out a survey. What is your name?")


# 2. Process name step
@client.on_message(filters.state(UserSurvey.name))
async def process_name(client: MaxClient, message: Message):
    # Store temporary state data
    await client.fsm.update_data(message.chat_id, message.sender_id, name=message.text)
    # Move to next state
    await client.fsm.set_state(message.chat_id, message.sender_id, UserSurvey.age)
    await message.reply(f"Nice to meet you, {message.text}! How old are you?")


# 3. Process age step
@client.on_message(filters.state(UserSurvey.age))
async def process_age(client: MaxClient, message: Message):
    if not message.text.isdigit():
        return await message.reply("Please enter your age as a number.")

    await client.fsm.update_data(message.chat_id, message.sender_id, age=int(message.text))
    await client.fsm.set_state(message.chat_id, message.sender_id, UserSurvey.city)
    await message.reply("Which city do you live in?")


# 4. Process city step and finish
@client.on_message(filters.state(UserSurvey.city))
async def process_city(client: MaxClient, message: Message):
    data = await client.fsm.update_data(message.chat_id, message.sender_id, city=message.text)
    
    # Clear state upon completion
    await client.fsm.clear(message.chat_id, message.sender_id)

    await message.reply(
        "Survey completed successfully!\n"
        f"Name: {data['name']}\n"
        f"Age: {data['age']}\n"
        f"City: {data['city']}"
    )


# 5. Cancel command at any step
@client.on_message(filters.command("cancel") & ~filters.state(None))
async def cancel_handler(client: MaxClient, message: Message):
    await client.fsm.clear(message.chat_id, message.sender_id)
    await message.reply("Survey cancelled.")


if __name__ == "__main__":
    client.run()
```

---

## 3. FSM Management Methods

- `await client.fsm.set_state(chat_id, user_id, state)` — set state for user in chat.
- `await client.fsm.get_state(chat_id, user_id)` — get active state string.
- `await client.fsm.update_data(chat_id, user_id, **kwargs)` — write or update temporary state variables.
- `await client.fsm.get_data(chat_id, user_id)` — retrieve dictionary of stored data.
- `await client.fsm.clear(chat_id, user_id)` — reset state and wipe stored data.
