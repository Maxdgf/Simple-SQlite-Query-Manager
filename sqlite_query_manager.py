'''
============================================
|GUI Менеджер sqlite запросов     by Maxdgf|
============================================
'''

#необходимые библиотеки
import os
import sqlite3
import tkinter as tk
import pandas as pd
from tabulate import tabulate
from tkinter import ttk, filedialog, messagebox, StringVar
from async_tkinter_loop import async_handler, async_mainloop
from tkinter.scrolledtext import ScrolledText

#async_tkinter_loop = библиотека поддерживающая асинхронность в tkinter
#tabulate = бибилиотека для красивого текстового табличного вывода

#класс приложения
class SqliteQueryManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        #===============================================Константы
        self.DB_CONNECTION_TIMEOUT = 5
        #===============================================Константы

        #=============================================================================================Окно(настройка)
        self.title("Sqlite db query manager")
        self.geometry("500x500")
        #=============================================================================================Окно(настройка)

        #============================================================================Переменные состояния
        self.selected_db = StringVar(self)
        self.user_query = StringVar(self)
        #============================================================================Переменные состояния

        #=============================================================================================UI

        #--------------------------------------------------------------------Поле выбора файла бд
        db_file_selection_frame = ttk.Frame(self)

        ttk.Label(db_file_selection_frame, text="Please, select db file here: ").pack(side="left")

        select_button = ttk.Button(db_file_selection_frame, text="select db file", command=self.pick_db_file)
        select_button.pack(side="left")
        selected_db_file_view = ttk.Label(db_file_selection_frame, textvariable=self.selected_db)
        selected_db_file_view.pack(side="left")

        db_file_selection_frame.pack(fill="x")
        #--------------------------------------------------------------------Поле выбора файла бд

        #--------------------------------------------------------------------Поле ввода запроса
        query_frame = ttk.Frame(self)

        query_input = ttk.Entry(query_frame, textvariable=self.user_query, foreground="green")
        query_input.pack(side="left", fill="x", expand=True)
        query_buttton = ttk.Button(query_frame, text="execute", command=async_handler(self.execute_query))
        query_buttton.pack(side="left")

        query_frame.pack(fill="x")
        #--------------------------------------------------------------------Поле ввода запроса

        ttk.Label(text="Query result here:").pack()

        #--------------------------------------------------------------------Поле результата запроса
        self.query_result_field = ScrolledText(self, relief=tk.GROOVE, wrap=tk.NONE, foreground="lime")
        self.query_result_field.pack(expand=True, fill="both")
        horizontal_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.query_result_field.xview)
        horizontal_scrollbar.pack(fill="x")
        self.query_result_field.config(xscrollcommand=horizontal_scrollbar.set, bg="black")
        #--------------------------------------------------------------------Поле результата запроса

        #=============================================================================================UI

    #==========================================================================================================Функции
    def clear_query_output_field(self): self.query_result_field.delete("1.0", "end") #очистка поля результата запроса

    #функция захвата файла .db из файловой системы с помощью tkinter filedialog
    def pick_db_file(self):
        db_path = filedialog.askopenfilename(title="Select DB file", filetypes=[("DB file", "*.db"), ("All files", "*.")])

        if len(db_path) > 0:
            if os.path.exists(db_path):
                self.selected_db.set(db_path)
                messagebox.showinfo("Info", "Db file selected!")
            else:
                messagebox.showerror("Error", "Db file path not exists!")
        else:
            messagebox.showwarning("Warning", "Db file not selected!")

    #асинхронная функция для выполнения запроса к бд(не перегружающая главный поток программы)
    async def execute_query(self):
        try:
            self.clear_query_output_field() #очищаем поле для нового результата

            if len(self.selected_db.get()) > 0:
                #подключаемся, создаём курсор
                connection = sqlite3.connect(self.selected_db.get(), timeout=self.DB_CONNECTION_TIMEOUT)
                cursor = connection.cursor()

                cursor.execute(self.user_query.get()) 
                connection.commit() #сохраняем изменения
                
                result = cursor.fetchall()
                connection.close() #закрываем подключение

                df = pd.DataFrame(result)
                result_table = tabulate(df, headers="keys", tablefmt="grid")

                if len(result_table) > 0: #проверяем, не пуст ли результат
                    self.query_result_field.insert("1.0", result_table)
                    messagebox.showinfo("Info", f"Your query:\n[{self.user_query.get()}]\ncompleted succesfully! See result now)))")
                else:
                    messagebox.showwarning("Warning", f"Your query:\n[{self.user_query.get()}]\ncompleted succesfully, but query result is empty(")
            else:
                messagebox.showerror("Error", "Please, select db file.")    
        except Exception as e:
            messagebox.showerror("Error", f"Query execution failed.\nexception:\n{e}")
    #==========================================================================================================Функции

if __name__ == "__main__":
    sqliteQueryManagerApp = SqliteQueryManagerApp() #инициализируем класс приложения
    async_mainloop(sqliteQueryManagerApp) #запуск главного асинхронного цикла приложения(необходимо для работы асинхронных функций)

