from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll


class VkMessenger:
    def __init__(self, token, login, password, id):
        self.id = id
        self.token = token
        self.vk = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_session = vk_api.VkApi(login, password)
        self.api = None
        self.user = {}

    def write_msg(self, user_id, message=None, attachment=None):
        """
        отправка сообщений
        attach не обязательный параметр
        """
        if message is None and attachment is None:
            return False
        if attachment:
            if message:
                self.vk.method('messages.send', {'user_id': user_id, 'message': message,
                                                 'attachment': attachment,
                                                 'random_id': randrange(10 ** 7)})
            else:
                self.vk.method('messages.send', {'user_id': user_id,
                                                 'attachment': attachment,
                                                 'random_id': randrange(10 ** 7)})
        else:
            self.vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)})

    def get_user_data(self, user_id, token=''):
        """
        получение параметров пользователя для поиска(возраст, пол, др и т.д.)
        :param user_id: ид пользователя чьи данные будем брать
        :param token: если профиль пользователя закрыт, то Мы попросим его дать нам ссылку с токеном на доступ
        :return:
        """
        if not bool(token):
            # этот запрос отработает при первой попытке и из этих данных Мы поймем надо ли запрашивать токен
            user = self.vk.method("users.get", {"user_ids": user_id, "fields": "sex, bdate, city, country, relation"})
        else:
            # вот тут выяснилось что нужно присвоить токен пользователя в свойство класса для зароса данных профиля
            self.vk = vk_api.VkApi(token=token)
            user = self.vk.method("users.get", {"user_ids": user_id, "fields": "sex, bdate, city, country, relation"})
            # ну а здесь обратно вернем наш токен
            self.vk = vk_api.VkApi(token=self.token)
        if (user[0].get('is_closed') is True and token is None) \
                or not user[0].get('bdate') or str(user[0].get('bdate')).count('.') < 2:
            return False
        first_name = user[0].get('first_name')
        last_name = user[0].get('last_name')
        sex = user[0].get('sex')
        bdate = user[0].get('bdate')
        city = user[0].get('city')
        city_id = 0
        if bool(city):
            city_id = city.get('id')
        country = user[0].get('country')
        country_id = 0
        if bool(country):
            country_id = country.get('id')
        relation = user[0].get('relation')
        # пока не пригодилось
        # city_title = user[0].get('city').get('title')
        # country_title = user[0].get('country').get('title')

        # сохраним
        self.user = {'user_id': user_id,
                     'first_name': first_name,
                     'last_name': last_name,
                     'sex': sex,
                     'bdate': bdate,
                     'city_id': city_id,
                     'country_id': country_id,
                     'relation': relation,
                     'token': token}
        return self.user

    def get_variable(self, start_pos=0, user_data=None):
        """
        отправить варианты найденных профилей пользователю
        """
        age = 25
        if user_data is None:
            # пока не пригодились
            # first_name = self.user.get('first_name')
            # last_name = self.user.get('last_name')
            # relation = self.user.get('relation')
            sex = self.user.get('sex')
            # меняем пол(искать нужно противоположный)
            if sex == 1:
                sex = 2
            elif sex == 2:
                sex = 1
            bdate = self.user.get('bdate')
            if bool(bdate) and len(bdate) == 10:
                age = 2021 - int(bdate.rpartition('.')[2])
            city_id = self.user.get('city_id')
            country_id = self.user.get('country_id')
            user_token = self.user.get('token')
        else:
            sex = user_data.get('sex')
            # меняем пол(искать нужно противоположный)
            if sex == 1:
                sex = 2
            elif sex == 2:
                sex = 1
            bdate = str(user_data.get('bdate'))
            if bool(bdate) and len(bdate) == 10:
                age = 2021 - int(bdate.partition('-')[0])
            city_id = user_data.get('city_id')
            country_id = user_data.get('country_id')
            user_token = user_data.get('token')
        print(city_id)
        if city_id is None:
            city_id = 0
        if country_id:
            country_id = 0
        if bool(user_token):
            self.vk_session = vk_api.VkApi(token=user_token)
        else:
            try:
                self.vk_session.auth(token_only=True)
            except vk_api.AuthError as error_msg:
                print('error in Auth')
                print(error_msg)

        self.api = self.vk_session.get_api()
        found = self.api.users.search(sort=0,
                                      offset=start_pos,
                                      count=10,
                                      sex=sex,
                                      city=city_id,
                                      country=country_id,
                                      age_from=age - 3,
                                      age_to=age + 3,
                                      online=1,
                                      has_photo=1,
                                      status=6,
                                      fields="domain, is_closed")
        # вариант, мне кажется, далеко не самый лучший для увеличения количества результатов поиска, но тоже вариант
        if bool(user_token):
            self.vk_session = vk_api.VkApi(token=user_token)
        return found

    def get_info(self, found):
        # по профилям полученных из результата поиска пройдем и фото соберем
        for_send = []
        for prof_id in found:
            # возьмем фото из профиля
            photos_prof = self.api.photos.get(owner_id=prof_id, album_id='profile', extended=1,
                                              feed_type="photo", photo_sizes=0)
            # и со стены тоже возьмем
            photos_wall = self.api.photos.get(owner_id=prof_id, album_id='wall', extended=1,
                                              feed_type="photo", photo_sizes=0)
            # заготовки
            ph1_id = ''
            ph1_oid = ''
            ph1_level = 0
            ph2_id = ''
            ph2_oid = ''
            ph2_level = 0
            ph3_id = ''
            ph3_oid = ''
            ph3_level = 0
            all_photo = []
            # соберем все фото в одну кучу
            for photo in photos_prof['items']:
                all_photo.append({'sizes': photo['sizes'],
                                  'level': photo['likes']['count'] + photo['comments']['count'],
                                  'id': photo['id'], 'oid': photo['owner_id']})
            for photo in photos_wall['items']:
                all_photo.append({'sizes': photo['sizes'],
                                  'level': photo['likes']['count'] + photo['comments']['count'],
                                  'id': photo['id'], 'oid': photo['owner_id']})
            # Теперь пробежимся по ним и выберем 3 самые популярные(кол-во комментов + кол-во лайков)
            for item in all_photo:
                if item['level'] > ph1_level:
                    ph3_id = ph2_id
                    ph3_oid = ph2_oid
                    ph3_level = ph2_level
                    ph2_id = ph1_id
                    ph2_oid = ph1_oid
                    ph2_level = ph1_level
                    ph1_level = item['level']
                    ph1_id = item['id']
                    ph1_oid = item['oid']
                elif item['level'] > ph2_level:
                    ph3_id = ph2_id
                    ph3_oid = ph2_oid
                    ph3_level = ph2_level
                    ph2_level = item['level']
                    ph2_id = item['id']
                    ph2_oid = item['oid']
                elif item['level'] > ph3_level:
                    ph3_level = item['level']
                    ph3_id = item['id']
                    ph3_oid = item['oid']
            # если нет даже одного фото, то не будем отправлять
            if bool(ph1_oid):
                # добавим в список на отправку
                for_send.append({'prof_id': prof_id,
                                 'link': f"https://vk.com/id{prof_id}",
                                 'attach': 'photo' + str(ph1_oid) + '_' + str(ph1_id) + ',' +
                                           'photo' + str(ph2_oid) + '_' + str(ph2_id) + ',' +
                                           'photo' + str(ph3_oid) + '_' + str(ph3_id)})
        return for_send