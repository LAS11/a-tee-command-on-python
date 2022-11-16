# скрипт для подключения к консольной программе,
# приёма данных из stdout-канала
# и их запись в txt-файл
# на примере подключения к программе для работы 
# с серверами игра на Source Engine srcds_win64.exe
# по сути, попытка реализовать функционал unix-команды 'tee' средствами питона

from datetime import datetime
import os
import subprocess
import concurrent.futures
import time

#генерация имени будущего лог-файла
def get_log_name():
	log_name = ""
	today = datetime.today()
	ww = today.isocalendar()[1]  #номер текущей недели
	YY = today.year
	monday = datetime.fromisocalendar(YY, ww, 1)
	sunday = datetime.fromisocalendar(YY, ww, 7)

    #лог поненедельно (1 файл - 1 неделя)
	log_name = "Week №" + str(ww) + " (" + str(monday.day) + "." + str(monday.month) + "." + str(
		monday.year) + "-" + str(sunday.day) + "." + str(sunday.month) + "." + str(sunday.year) + ")"
	return log_name

#получение режима работы с файлом исходя из того, существует ли требуемый лог-файл в папке
def get_open_mode():
	if (os.path.isfile(log_path + log_name + ".log")):
		return ("a")
	else:
		return ("w")

#запись строки в лог-файл
def write_string_to_log(log, log_string):
	if (log_string != ''):
		today = datetime.today()
  
		log_string_time = str(today.time()) + " " + str(today.date())
		log_string_new = (log_string.encode('cp1251', 'xmlcharrefreplace')).decode("utf-8")
        
		log.write('{0:<120s}   {1:>10s}'.format(log_string_new[0:-1], log_string_time) + "\n")
	return 1

#вывод полученной строки в консоль
#добавлено, т.к. при приёме данных из stdout-канала srcds_win64.exe
#тот перестаёт выводить что-либо
def display_string(log_string):
	log_string_new = (log_string.encode('cp1251', 'xmlcharrefreplace')).decode("utf-8") #перекодирование принятой строки из cp1251 в utf-8
	print(log_string_new, end='')
	return 1


TIME_TO_RESTART = 5  #время до перезапуска сервера (секунды)

#начало работы скрипта
#перед стартом проверяется, есть ли исполняемый файл в папке с сервером
if (os.path.isfile(os.getcwd() + '\srcds_win64.exe') == True):
	log_name = get_log_name()
	log_path = os.getcwd() + "\logs" + "\\"
	if (os.path.isdir(log_path) == False):
		os.mkdir(log_path)
   
	with open(log_path + log_name + ".log", get_open_mode(), 1) as log:
		srv = subprocess.Popen([
			'srcds_win64.exe', '-game', 'garrysmod', '-port', '27015', '-tickrate', '20', '+host_thread_mode', '2',
			'-threads', '2', '-console', '-condebug'
			'norestart', '-nohltv', '+host_workshop_collection', '414788549'
		],
			shell=False,
			startupinfo=None,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			stdin=None,
			creationflags=0,
			text=True)
		log.write("\n---Запуск сервера: " + str(datetime.today()) + "---\n\n")
		server_status = True

        #простенькая попытка в многопоточность
		with concurrent.futures.ThreadPoolExecutor() as executor:
			while (server_status == True):
				if (srv.poll() == None): #subprocess.poll() возвращает None, если приложение не запущено
					log_string = srv.stdout.readline()
                    
					display_string_t = executor.submit(display_string, log_string)
					write_to_log_t = executor.submit(write_string_to_log, log, log_string)
					log_cycle = (display_string_t.result() and write_to_log_t.result())

				else:
					write_to_log_t.cancel()
					display_string_t.cancel()
                    
					if (srv.poll() == 0): #subprocess.poll() возвращает 0 при остановке приложения
						server_status = False
						log.write("\n---Остановка сервера пользователем: " + str(datetime.today()) + "---\n\n")
						print("\n---Остановка сервера пользователем---")
						input("Нажмите Enter для завершения работы...")
                        
                    #перезапуск сервера при его краше (интервал по умолчанию 5 сек)
					elif (srv.poll() != 0): #subprocess.poll() возвращает не 0 при аварийной остановке приложения
						log.write("\n---Сбой работы сервера: " + str(datetime.today()) + "---")
						log.write("\n---Перезапуск через " + str(TIME_TO_RESTART) + " сек---\n\n")
                        
						print("\n---Сбой работы сервера. Перезапуск через " + str(TIME_TO_RESTART) + " сек...")
						time.sleep(TIME_TO_RESTART)
                        
						srv = subprocess.Popen([
							'srcds_win64.exe', '-game', 'garrysmod', '-port', '27015', '-tickrate', '20',
							'+host_thread_mode', '2', '-threads', '2', '-console', '-condebug'
							'norestart', '-nohltv', '+host_workshop_collection', '414788549'
						],
							shell=False,
							startupinfo=None,
							stdout=subprocess.PIPE,
							stderr=subprocess.STDOUT,
							stdin=None,
							creationflags=0,
							text=True)
                            
						log.write("\n---Перезапуск сервера: " + str(datetime.today()) + "---\n\n")
else:
	input("Исполняемый файл сервера не найден, кекв. Он точно есть в папке со скриптом?\n")
