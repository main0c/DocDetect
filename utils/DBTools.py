import sqlite3
from utils.debug import DBG

class DBTool():
    def sqltest():
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        # cursor.execute('create table user (id varchar(20) primary key, name varchar(20))')
        cursor.execute('insert into user (id, name) values (\'3\', \'Michael\')')
        cursor.rowcount
        cursor.close()
        conn.commit()
        conn.close()

        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        # 执行查询语句:
        cursor.execute('select * from user where id=?', ('1',))
        # 获得查询结果集:
        values = cursor.fetchall()
        cursor.close()
        conn.close()

        def create_table():
            c.execute('CREATE TABLE IF NOT EXISTS stuffToPlot(unix REAL, datestamp TEXT, keyword TEXT, value REAL)')

        def data_entry():
            c.execute("INSERT INTO stuffToPlot VALUES(145123452, '2016-01-01', 'Python',5)")
            conn.commit()
            c.close()
            conn.close()

        def dynamic_data_entry():
            unix = time.time()
            date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H: %M :%S'))
            keyword = 'Python'
            value = random.randrange(0, 10)
            c.execute("INSERT INTO stuffToPlot (unix, datestamp, keyword, value) VALUES (?, ?, ?, ?)",
                      (unix, date, keyword, value))
            conn.commit()

        def read_from_db():
            c.execute("SELECT * FROM stuffToPlot WHERE value=3 AND keyword='Python'")
            #  data = c.fetchall()
            # print(data)
            for row in c.fetchall():
                print(row)

    def saveEvent1():
        DBG ("Someone is closing to No 1  !")
    def saveEvent2():
        DBG ("Someone is closing to No 2  !")
