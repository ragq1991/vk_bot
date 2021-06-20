import psycopg2


class DBForBot:
    def __init__(self, dbname, user, password, host):
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        self.cursor = self.conn.cursor()

    def add_user(self, user_id, data):
        if self.get_params(user_id) is False:
            sql = ('insert into users (vk_id, first_name, last_name, sex, bdate, city_id, country_id, relation, token)'
                   'values (%s, %s, %s, %s, %s, %s, %s, %s, %s)')
            record = (user_id,
                      data['first_name'],
                      data['last_name'],
                      data['sex'],
                      data['bdate'],
                      data['city_id'],
                      data['country_id'],
                      data['relation'],
                      data['token'])
            self.cursor.execute(sql, record)
            self.conn.commit()
            return True
        else:
            return False

    def get_params(self, user_id):
        self.cursor.execute('select * from users where vk_id = %s', [user_id])
        res = self.cursor.fetchone()
        if res is not None:
            user_data = {'user_id': res[1],
                         'first_name': res[2],
                         'last_name': res[3],
                         'sex': res[4],
                         'bdate': res[5],
                         'city_id': res[6],
                         'country_id': res[7],
                         'relation': res[8],
                         'token': res[9]}
            return user_data
        return False

    def insert_searches(self, user_id, found_id):
        res = self.get_searches(user_id)
        for item in res:
            if item[0] == found_id:
                return False
        sql = 'insert into searches (for_id, vk_id, showed) values (%s, %s, True)'
        record = (user_id, found_id)
        self.cursor.execute(sql, record)
        self.conn.commit()
        return True

    def get_searches(self, user_id):
        self.cursor.execute('select vk_id from searches where for_id = %s', [user_id])
        return self.cursor.fetchall()

    def searches_before(self, user_id, searched_id):
        self.cursor.execute('select * from searches where for_id = %s and vk_id = %s', [user_id, searched_id])
        return bool(self.cursor.fetchall())

    def get_bl(self, user_id):
        self.cursor.execute('select vk_id from searches where for_id = %s and black_list = True', [user_id])
        return self.cursor.fetchall()

    def get_fav(self, user_id):
        self.cursor.execute('select vk_id from searches where for_id = %s and favorite = True', [user_id])
        return self.cursor.fetchall()

    def get_show(self, user_id):
        self.cursor.execute('select vk_id from searches where for_id = %s and showed = True', [user_id])
        return self.cursor.fetchall()

    def add_to_bl(self, for_id, bl_id):
        sql = 'update searches set black_list = True where for_id = %s and vk_id = %s'
        record = (for_id, bl_id)
        self.cursor.execute(sql, record)
        self.conn.commit()

    def add_to_fav(self, for_id, fav_id):
        sql = 'update searches set favorite = True where for_id = %s and vk_id = %s'
        record = (for_id, fav_id)
        self.cursor.execute(sql, record)
        self.conn.commit()
