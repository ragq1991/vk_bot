from VkMessenger import VkMessenger
from DBForBot import DBForBot
from vk_api.longpoll import VkEventType
from Dicts_of_word import list_hello, list_yes, list_no
from time import sleep
import settings as stt


def send(test_db, my_vk, user_id, user_data):
    my_vk.write_msg(user_id, 'Идет поиск...')
    # запомним пользователя
    if str(user_data['bdate']).count('.') < 2 and str(user_data['bdate']).count('-') < 2:
        user_data['bdate'] = '1995-01-01'
    test_db.add_user(user_id, user_data)
    # далее зациклимся для поиска профилей которые ранее НЕ отправлялись пользователю
    get_profile = False
    position = 0
    list_for_send = []
    while not get_profile:
        # получим список найденных
        found = my_vk.get_variable(position, user_data)
        # исключим закрытые профили и те что уже ранее отправлялись
        for ids in found['items']:
            if ids['is_closed'] is False:
                if not test_db.searches_before(user_id, ids['id']):
                    list_for_send.append(ids['id'])
        if len(list_for_send) > 2:
            get_profile = True
        else:
            position += 10
    data_for_send = my_vk.get_info(list_for_send)
    for i in range(3):
        my_vk.write_msg(user_id, data_for_send[i]['link'], data_for_send[i]['attach'])
        test_db.insert_searches(user_id, data_for_send[i]['prof_id'])
    my_vk.write_msg(user_id, 'Для получения следующих вариантов отправьте слово "go".')


def no_access(my_vk, user_id):
    my_vk.write_msg(user_id, "Уважаемый пользователь, данные Вашего профиля необходимые для "
                             "работы БОТа закрыты.")
    my_vk.write_msg(user_id, "Что бы дать нам доступ пройдите по ссылке в следующем сообщении,"
                             " нажмите кнопку разрешить и отправьте URL на который Вас отправит"
                             " Вконтакте")
    my_vk.write_msg(user_id, f"https://oauth.vk.com/authorize?"
                             f"client_id={my_vk.id}&display=page&"
                             "redirect_uri=https://oauth.vk.com/blank.html&"
                             "scope=friends,notify,photos,wall,email,mail,groups,stats,offline&"
                             "response_type=token&v=5.131")


def user_say_yes(test_db, my_vk, user_id):
    # получим параметры пользователя для будущего поиска из БД
    user_data = test_db.get_params(user_id)
    # если в БД нет попробуем взять с аккаунта Вконтакте
    if user_data is False:
        user_data = my_vk.get_user_data(user_id)
        # получили - запишем в БД
        if bool(user_data):
            send(test_db, my_vk, user_id, user_data)
        # не получили - сообщим что доступа нет и нужен токен
        else:
            no_access(my_vk, user_id)
    # нашелся такой в БД, отправим ему анкеты
    else:
        send(test_db, my_vk, user_id, user_data)


def user_send_token(test_db, my_vk, user_id, request):
    # сообщим пользователю что получили его токен
    my_vk.write_msg(user_id, "Ссылку получил, обрабатываю...")
    token = request.partition('access_token=')[2].partition('&')[0]
    # получим данные из аккаунта Вконтакте с токеном пользователя
    user_data = my_vk.get_user_data(user_id, token)
    if bool(user_data):
        # полуили данные - отправим анкеты
        send(test_db, my_vk, user_id, user_data)
    else:
        # не получили - сообщим пользователю
        no_access(my_vk, user_id)


def main():
    # создадм объект для общания с БД
    test_db = DBForBot(stt.db_name, stt.db_user, stt.db_pass, stt.db_host)
    # создадим объект для API Вконтакте
    my_vk = VkMessenger(stt.vk_token, stt.vk_login, stt.vk_pass, stt.vk_idapp)
    # слушаем входящие сообщения
    for event in my_vk.longpoll.listen():
        # если что-то написали
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            # если это "что-то" написали Нам
            if event.to_me:
                # получим это "что-то" и id отправителя
                request = event.text
                user_id = event.user_id
                # если с нами поздоровались - поздороваемся в ответ
                if request.lower() in list_hello:
                    my_vk.write_msg(user_id, "Хай.")
                    my_vk.write_msg(user_id, "Найдем тебе собеседника?")
                elif request.lower() in list_yes:
                    user_say_yes(test_db, my_vk, user_id)
                elif request.lower() in list_no:
                    my_vk.write_msg(event.user_id, "Ну тогда пока.")
                elif 'access_token' in request:
                    user_send_token(test_db, my_vk, user_id, request)
                else:
                    my_vk.write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == "__main__":
    while True:
        try:
            main()
        except:
            sleep(3)
