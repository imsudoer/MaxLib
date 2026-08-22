from maxlib import MaxClient as Client
from maxlib.filters import filters
from maxlib.classes import Message

client = Client("me")

@client.on_connect
def onconnect():
    for i in range(100):
        try:
            usr = client.get_user(id=i)
            client.send_message(usr.chat.id, "Hi! It's a test spam-message. Report me.")
        except:
            pass