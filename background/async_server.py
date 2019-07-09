# coding=utf-8
import asyncio, socket
import _thread
import telebot
import time
import json
from bitstring import BitArray
from datetime import datetime

import os, sys
import django

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# load channels layer and django environment
sys.path.append('/app')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "thisisproject.settings")
django.setup()
channel_layer = get_channel_layer()

# settings variables
TOKEN = ''  # put your bot token here
DUTY = set()

with open('background/duty.txt', encoding='utf8') as f:
    for line in f.readlines():
        DUTY.add(line[:-1])

with open("background/config.json", "r", encoding='utf8') as read_file:
    CONFIG = json.load(read_file)

with open("background/sensors.json", "r", encoding='utf8') as read_file:
    SENSORS = json.load(read_file)

print(f'[SERVER STARTED at {socket.gethostbyname(socket.gethostname())}]')


# send data to channels layer from loop
async def senddata(loc, message):
    await channel_layer.group_send(
        "events", {"type": "events.event", "text": message, "location": loc, "mode": "success"}
    )


# alert event timer
def timer(start, message, addr, id):
    """
    Alert event timer. Started after button down until release.
    """
    if start:
        while True:
            time.sleep(0.01)
            if SENSORS[addr][id][1] == 'true':
                break
            if time.time() - start > 4:
                now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
                print(f"[{now}]:[{message}]: ALERT")
                for chatid in CONFIG['access']:
                    tb.send_message(chatid, f"{message}: ALERT")
                    async_to_sync(channel_layer.group_send)(
                        "events", {"type": "events.event", "text": "ALERT", "location": message, "mode": "danger"}
                    )
                break
            else:
                continue


async def handle_client(client, addr):
    """
    Events handler for clients.
    """
    while True:
        try:
            request = await loop.sock_recv(client, 64)
            state = str(BitArray(request))
            commands = list(map(''.join, zip(*[iter(state[2:])] * 6)))
            start = time.time()
            now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
            for command in commands:
                try:
                    # t1 = threading.Thread(target=timer,
                    #                       args=(start, SENSORS[addr[0]][command[-3]][0], addr[0], state[-3]))
                    if command[-1] == '0':
                        SENSORS[addr[0]][command[-3]][1] = 'false'
                        _thread.start_new_thread(timer, (start, SENSORS[addr[0]][command[-3]][0], addr[0], command[-3]))
                        print(f"[{now}]:[{SENSORS[addr[0]][command[-3]][0]}]: button DOWN")
                        for chatid in DUTY:
                            tb.send_message(chatid, f"{SENSORS[addr[0]][command[-3]][0]}: нажата кнопка")
                            loop.create_task(senddata(SENSORS[addr[0]][command[-3]][0], "нажата кнопка"))
                    if command[-1] == '1':
                        SENSORS[addr[0]][command[-3]][1] = 'true'
                        print(f"[{now}]:[{SENSORS[addr[0]][command[-3]][0]}]: button UP")
                except Exception as e:
                    print(e)
        except:
            print(f'[{now}]:[SERVER]: {addr} - DISCONNECTED')
            break
    client.close()


async def run_server():
    while True:
        try:
            client, addr = await loop.sock_accept(server)
            now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
            print(f'[{now}]:[SERVER]: {addr} - CONNECTED')
            loop.create_task(handle_client(client, addr))
        except:
            print('error')


def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        chatid = str(m.chat.id)
        message = m.text.lower()
        now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
        print(f"[{now}]:[{chatid}]: {m.text}")
        if chatid in CONFIG['access'] and m.content_type == 'text':
            if chatid not in DUTY:
                if message in {'привет', 'добрый день', 'Здравствуйте', 'ку'}:
                    DUTY.add(chatid)
                    print(f"[{now}]:[SERVER]: {chatid} - added to duty list")
                    with open('duty.txt', mode='w', encoding='utf8') as f:
                        for a in DUTY:
                            f.write(f'{a}\n')
                        f.close()
                    tb.send_message(chatid, f'Здравствуйте! Вы взяты на дежурство.')
            else:
                if message in {'пока', 'до свидания'}:
                    DUTY.remove(chatid)
                    print(f"[{now}]:[SERVER]: {chatid} - removed from duty list")
                    with open('duty.txt', mode='w', encoding='utf8') as f:
                        for a in DUTY:
                            f.write(f'{a}\n')
                    tb.send_message(chatid, f'Вы сняты с дежурства.\nНе забудьте выключить оборудование.\nДо свидания!')


def start_bot(addr, port):
    tb.set_update_listener(listener)
    while True:
        try:
            tb.polling(none_stop=True)
            tb.polling(interval=3)
            print('connected')
        except Exception as e:
            print(f'Connection error. Exception: {e}')
            time.sleep(1)


tb = telebot.TeleBot(TOKEN)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((socket.gethostbyname(socket.gethostname()), int(CONFIG['server'][1])))
server.listen(8)
server.setblocking(False)

loop = asyncio.get_event_loop()

if TOKEN:
    _thread.start_new_thread(start_bot, ('localhost', 9090))

try:
    loop.run_until_complete(run_server())
except KeyboardInterrupt:
    server.close()
