
# coding: utf-8

# In[1]:


import sys
sys.path.append("/home/ubuntu/ai_community/chat_sup")
import config
import telebot
from telebot import types
import pandas as pd
import numpy as np
import time
from Sqlite_bot import SQLighter
import datetime
from pytz import timezone
import shelve


# In[2]:


bot = telebot.TeleBot(config.token) # объект чат бота
db = SQLighter(config.db_path) # объект через который проходит общение с БД


# In[3]:


@bot.message_handler(commands=['start'])
def start(message):
    db = SQLighter(config.db_path)
    if db.check_user(message.from_user.id)==False:
        db.add_user("('"+str(message.from_user.id)+"')")
        for t in zip(['first_name', 'last_name', 'username'],
                     [message.from_user.first_name, message.from_user.last_name, message.from_user.username]):
            today = datetime.datetime.now(timezone('Europe/Moscow'))
            db.insert_into_table(name_of_table = 'anketa', 
                                 columns = ('user_id','anketa_field','value','value_date'), 
                                 values = (message.from_user.id, t[0], t[1],today.isoformat()))
    bot.send_message(message.chat.id,'Добро пожаловать в ai comunity!\n/events -     узнать о грядущих мероприятиях\n/form - заполнить анкету участника\n/my_user_id - узнать свой ID в базе')


# In[4]:


# Вспомогательные сущности для анкетирования
quetions_n = {'name':1,
              'surname':2,
              'edu':3,
              'work':4,
              'position':5,
              'phone':6,
              'email':7}

quetions = {'name':'Отлично! Назови, пожалуйста, свое имя...',
'surname':'Я в экстазе! Теперь напиши, пожалуйста, свою фамилию...',
'edu':'Раз уж мы так разоткровенничили, то где ты учился?',
'work':'Молодец! А где работаешь?',
'position':'Какая у тебя должность?',
           'phone':'Напиши, пожалуйста, свой номер телефона, что бы мы могли с тобой связаться',
           'email':'И почту, что бы не потеряться, когда telegram окончательно заблокируют'}


# In[5]:


def check_shelve(user_id):
    try:
        return shelve.open(config.action_shelve)[str(user_id)]
    except:
        return None


# In[6]:


@bot.message_handler(commands=['form'])
def form(message):
    with shelve.open(config.action_shelve) as storage:
        storage[str(message.from_user.id)] = list(quetions_n.keys())[0]
        bot.send_message(message.chat.id,quetions[storage[str(message.from_user.id)]])


# In[7]:


@bot.message_handler(content_types=['text'], 
                     func =lambda message: check_shelve(message.from_user.id) in 
                     quetions_n.keys())
def form_from_text(message):
    with shelve.open(config.action_shelve) as storage:
        if storage[str(message.from_user.id)]!= list(quetions.keys())[-1]:
            db = SQLighter(config.db_path)
            today = datetime.datetime.now(timezone('Europe/Moscow'))
            db.insert_into_table(name_of_table = 'anketa', 
                                 columns = ('user_id','anketa_field','value','value_date'), 
                                 values = (message.from_user.id, storage[str(message.from_user.id)], 
                                           message.text,today.isoformat()))
            storage[str(message.from_user.id)] = list(quetions_n.keys())            [quetions_n[storage[str(message.from_user.id)]]]
            bot.send_message(message.chat.id,quetions[storage[str(message.from_user.id)]])             
        else:
            del storage[str(message.from_user.id)]
            bot.send_message(message.chat.id,'Спасибо, закончили упражнение')


# In[8]:


@bot.message_handler(commands=['create_new_event'], 
                     func= lambda message:db.check_moderator(message.from_user.id))
def create_new_event(message):
    with shelve.open(config.action_shelve) as storage:
        storage[str(message.from_user.id)] = 'new_event'
    bot.send_message(message.chat.id,'в следующем сообщении введи описание события (4 поля, разделенные символом ;):\nдата события (yyyy-mm-dd);\nназвание события латиницей без пробелов;\nописание события\nмаксимальное количество участников')


# In[9]:


@bot.message_handler(content_types=['text'], 
                     func =lambda message: check_shelve(str(message.from_user.id))=='new_event')
def create_new_event_from_text(message):
    db = SQLighter(config.db_path)
    db.insert_into_table(name_of_table = 'events', 
                                 columns = ('date','name','descr','max_memb_count'), 
                                 values = (message.text.split(';')[0], 
                                           message.text.split(';')[1],
                                           message.text.split(';')[2],
                                           message.text.split(';')[3]))
    with shelve.open(config.action_shelve) as storage:
        del storage[str(message.from_user.id)]


# In[10]:


#today = datetime.datetime.now(timezone('Europe/Moscow'))
#[i[0] for i in pd.read_sql("select name from {0} where date>'{1}'".format('events',today.isoformat()), db.connection).values]


# In[11]:


@bot.message_handler(commands=['events'])
def events(message):
    keyboard = types.InlineKeyboardMarkup()
    today = datetime.datetime.now(timezone('Europe/Moscow'))
    db = SQLighter(config.db_path)
    keyboard.add(*[types.InlineKeyboardButton(text=i[0], callback_data=i[0]) 
                  for i in pd.read_sql("select name from {0} where date>'{1}'".format('events',
                                                                                   today.isoformat()), 
                                       db.connection).values])
    bot.send_message(message.chat.id,'Выбирай', reply_markup=keyboard)


# In[12]:


@bot.message_handler(commands=['my_user_id'])
def my_user_id(message):
    bot.send_message(message.chat.id,message.from_user.id)


# In[13]:


@bot.message_handler(commands=['admin'], func= lambda message:db.check_moderator(message.from_user.id))
def admin(message):
    bot.send_message(message.chat.id,'Поздравляю, ты админ, сейчас ты можешь только создать новое событие: инструкция по команде /create_new_event\nХочешь больше функций? Пиши этому парню: @d0naId')


# In[14]:


@bot.callback_query_handler(func=lambda call: SQLighter(config.db_path).check_event(call.data))
def callback_inline(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='зарегистрироваться на событие' +call.data, 
                                            callback_data='reg_event; '+call.data))
    db = SQLighter(config.db_path)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=pd.read_sql("select descr from events e where e.name='{0}'".format(call.data),
                                               db.connection).values,reply_markup=keyboard)


# In[ ]:


@bot.callback_query_handler(func=lambda call: call.data.split('; ')[0]=='reg_event' and
                            SQLighter(config.db_path).check_event(call.data.split('; ')[1]))
def reg_for_event(call):
    db = SQLighter(config.db_path)
    if pd.read_sql('select count(*) from {0} e where e.user_id = {1}'.format(call.data.split('; ')[1],
                                                                             call.from_user.id), 
                   db.connection).values[0][0]==0:
        db.reg_user_for_event(call.from_user.id,call.data.split('; ')[1])
        bot.send_message(call.message.chat.id, 'готово! ждем тебя на {}'.format(call.data.split('; ')[1]))
    else:
        bot.send_message(call.message.chat.id, 'Кажется, ты уже зарегистрирован на событие!')
        print(call.from_user)


# In[ ]:


if __name__ == '__main__':
    bot.polling(none_stop=True)

