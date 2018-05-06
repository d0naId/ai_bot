# coding: utf-8
import sqlite3
import pandas as pd
import numpy as np
import shelve
class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        
        # поля для основной таблички events
        self.fields = [['date', 'datetime'],['name', 'text'], ['descr', 'text'], ['max_memb_count', 'integer']]
        # поля для каждой из табличек
        self.fields_event = [['user_id', 'text'], ['status','text']]
    def create_table(self, name, fiels):
        self.cursor.execute('create table {0} ({1})'.format(name, ', '.join([' '.join(t) for t in fiels])))
        
    def insert_into_table(self, name_of_table, columns, values):
        self.cursor.execute('INSERT INTO {0} {1} VALUES {2}'.format(name_of_table,
                                                                      columns,
                                                                      values))
        self.connection.commit()
    def create_event(self, event_object):
        # Для каждого нового события создается новая табличка что бы записывать участников
        self.create_table(event_object['name'], [['user_id', 'text'], ['status','text']])
        # Для каждого события в табличку events добавляется строка
        self.insert_into_table('events', 
                               columns = tuple(pd.Series(event_object).dropna().index), 
                               values = tuple(pd.Series(event_object).dropna().values))
    def add_user(self, user_id): # метод, который добавляет пользователя в табличку users
        self.insert_into_table(name_of_table = 'users', columns="('user_id')", values=user_id)
        
    def check_user(self, user_id): # метод, который проверяет, есть ли пользователь в табличке users
        try:
            t = pd.read_sql('select count(*) from users u where u.user_id = {}'.format(user_id), self.connection)
            if t.values[0][0] == 1:
                return True
            elif t.values[0][0] >1:
                return 'WTF?'
            else:
                return False
        except:
            return False
    def check_event(self, event): # метод для проверки того, что событие есть вообще существует
        try:
            t = pd.read_sql("select count(*) from events e where e.name = '{}'".format(event), self.connection)
            if t.values[0][0] == 1:
                return True
            elif t.values[0][0] == 1:
                return 'WTF?'
            else:
                return False
        except:
            return False
    def reg_user_for_event(self, user, event):
        self.insert_into_table(event, columns=('user_id', 'status'), values=(user, 'first_reg'))
    def check_moderator(self, user_id):
        return(pd.read_sql('select is_moderator from {0} where user_id = {1}'.format('users', user_id), 
                           self.connection).values[0][0])