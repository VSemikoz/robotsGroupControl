# robotsGroupControl
Group control by robots (for example raspberry pi), through sockets in one network.


Открыть robotsGroupeControle/Socket и изменить 12 строку
        self.host = '192.168.1.243'
	на ip машины на которой запускается сервер
	
Запустить Server.py (команда quit закрыть серевер)

Запустить Client.py столько сколько надо

	Client.py ожидает на на вход ту карту с которой он будет работать(приемеры карт файлы 1 2 3)
	Далее клиенты ожидют ввод команд. Доступные:
	quit - закрыть клиент
	get_map - напечать карту в консоль
	send_map - отправить карту всем в сети, полученная карта будет напечатана в консоле при получении
	show_trg - показать набор целей полученный с карты
	show_pos - показать собственную позицию
	update_map - отправить запрос на обновление карты, после чего по некоторым алгоритмам запрос согласовывается или отвернается.
			Итогом команды является установление общей одинаковой карты для всех клиентов в сети.
	trg_dst - Начать распределение целей. Итог: каждый робот имет список (имя робота - имя цели)
	start_map_flow - Начать выполнение потока в котором с делеем в 5-7 секунд выполнятеся команда send_map
	start_update_flow - Начать выполнение потока в котором с делеем в 5-7 секунд выполнятеся команда update_map
	stop_map_flow - Завершает поток запущенный командой start_map_flow
	stop_update_flow - Завершает поток запущенный командой start_update_flow
	
Имеются случаи когда Server.py или Client.py не запускаются из за того что были некоректно закрыты.
В этом случае либо закрыть открытые процессы в фоне (рекомендуется) либо поменять порт в файле  robotsGroupeControle/Socket в строке 13
	        self.port = 263
Закрывать обе программы (Server и Client) нужно только через команду quit
