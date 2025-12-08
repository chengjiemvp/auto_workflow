import sqlite3
from log import output
from mapping_data import terminals_data, cy_locations_data


conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def create_table_if_not_exists():
    cursor.execute('''
                   create table if not exists terminals(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   firms_code TEXT NOT NULL UNIQUE,
                   TP_ID TEXT NOT NULL)
                   ''')
    cursor.execute('''
                   create table if not exists cy_locations(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   cy_code TEXT NOT NULL UNIQUE,
                   TP_ID TEXT NOT NULL)
                   ''')

create_table_if_not_exists()
conn.commit()

def insert_terminals_data():
    cursor.executemany('''INSERT OR IGNORE INTO terminals (firms_code, TP_ID) VALUES (?, ?)''', 
                       terminals_data
                       )

def insert_cy_locations_data():
    cursor.executemany('''INSERT OR IGNORE INTO cy_locations (cy_code, TP_ID) VALUES (?, ?)''',
                       cy_locations_data)

insert_terminals_data()
insert_cy_locations_data()

conn.commit()

cursor.execute("select * from terminals")
output("terminals table:")
for row in cursor.fetchall():
    print(row)

output("cy locations table:")
cursor.execute("select * from cy_locations")
for row in cursor.fetchall():
    print(row)

conn.close()
output("db closed")


# sessions table (id INTEGER PRIMARY KEY AUTOINCREMENT, 
#                   username TEXT,
#                   session_data TEXT NOT NULL,
#                   hostname TEXT,saved_at TEXT)
# gofreight_users table (id INTEGER PRIMATY KEY AUTOINCREMENT, 
#                           user TEXT PRIMARY KEY,
#                           pswd_encrypt TEXT NOT NULL)
