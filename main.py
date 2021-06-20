from VkMessenger import VkMessenger
from DBForBot import DBForBot
from vk_api.longpoll import VkEventType
from Dicts_of_word import list_hello, list_yes, list_no
from time import sleep

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


def main():
    test_db = DBForBot(dbname, user, password, host)
    my_vk = VkMessenger(token, login, password, id)
    for event in my_vk.longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.to_me:
                request = event.text
                user_id = event.user_id
                if request.lower() in list_hello:
                    my_vk.write_msg(user_id, "Хай.")
                    my_vk.write_msg(user_id, "Найдем тебе собеседника?")
                elif request.lower() in list_yes:
                    user_data = test_db.get_params(user_id)
                    if user_data is False:
                        user_data = my_vk.get_user_data(user_id)
                        if bool(user_data):
                            send(test_db, my_vk, user_id, user_data)
                        else:
                            no_access(my_vk, user_id)
                    else:
                        send(test_db, my_vk, user_id, user_data)
                elif 'access_token' in request:
                    my_vk.write_msg(user_id, "Ссылку получил, обрабатываю...")
                    token = request.partition('access_token=')[2].partition('&')[0]
                    user_data = my_vk.get_user_data(user_id, token)
                    if bool(user_data):
                        send(test_db, my_vk, user_id, user_data)
                    else:
                        no_access(my_vk, user_id)
                elif request.lower() in list_no:
                    my_vk.write_msg(event.user_id, "Ну тогда пока.")
                else:
                    try:
                        my_vk.write_msg(event.user_id, "Не поняла вашего ответа...")
                    except ValueError:
                        print('321')


if __name__ == "__main__":
    while True:
        try:
            main()
        except:
            sleep(3)

