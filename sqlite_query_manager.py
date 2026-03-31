'''
============================================
|GUI sqlite query manager         by Maxdgf|
============================================
'''

import sqlite3, os, time
import tkinter as tk
from tabulate import tabulate
from tkinter import ttk, filedialog, messagebox, StringVar, IntVar
from async_tkinter_loop import async_handler, async_mainloop
from tkinter.scrolledtext import ScrolledText
from typing import Literal
from collections import namedtuple

# async_tkinter_loop = support async in tkinter
# tabulate = text table output

class SqliteDbManager:
    # query result model
    # data: query result data
    # exception_message: possible exception message
    _QueryResult = namedtuple(
        "QueryResult", 
        ["data", "exception_message"]
    )

    def __init__(self) -> None:
        pass

    def __format_result_to_table(self, result: str) -> str:
        """
        Formats query result to text ascii table.

        Parameters:
        ------------

        result: result of query
        """
        import pandas as pd # import pandas
        df = pd.DataFrame(result) # convert to dataframe
        return tabulate(df, tablefmt="grid", showindex=False)

    def execute_query(self, db_path: str, query: str) -> _QueryResult:
        """
        Connects to db and executes query.

        Parameters:
        ------------

        db_path: path to db
        query: query to db
        """
        try:
            start_time = time.monotonic() # start time point

            connection = sqlite3.connect(db_path)
            cursor = connection.cursor()

            cursor.execute(query) #execute query
            connection.commit() # save changes

            result = [
                [column_name[0] for column_name in cursor.description] # get columns names
            ]
            result += cursor.fetchall() # add query result
            connection.close() # close connection

            end_time = time.monotonic() # end time point
            execution_time = end_time - start_time # calculate query execution time in seconds

            result = self.__format_result_to_table(result) # format result

            return self._QueryResult(data=f"{result}\n\nQuery was completed in {execution_time:.7f} sec", exception_message=None)
        except Exception as e:
            return self._QueryResult(data=None, exception_message=f"Exception occured: {e}")

class SqliteQueryManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        # Window config
        self.title("Sqlite db query manager")
        self.geometry("500x500")
        self.minsize(width=500, height=500)

        # State vars
        self.selected_db = StringVar(self)
        self.user_query = StringVar(self)
        self.query_execution_progress = IntVar(self)

        self.sqlite_db_manager = SqliteDbManager()

        #============================================================================================= UI

        # db file selection frame
        db_file_selection_frame = ttk.Frame(self)

        ttk.Label(db_file_selection_frame, text="Please, select db file here: ").pack(side="left")

        select_button = ttk.Button(db_file_selection_frame, text="select db file", command=self.pick_db_file)
        select_button.pack(side="left")
        selected_db_file_view = ttk.Label(db_file_selection_frame, textvariable=self.selected_db, font=("Arial", 10, "bold"))
        selected_db_file_view.pack(side="left")

        db_file_selection_frame.pack(fill="x")

        # query input frame
        query_frame = ttk.Frame(self)

        query_input = ttk.Entry(query_frame, textvariable=self.user_query, foreground="green")
        query_input.pack(side="left", fill="x", expand=True)
        self.query_big_input = ScrolledText(self, relief=tk.GROOVE, wrap=tk.NONE, foreground="lime")
        self.query_big_input.pack_forget()
        query_buttton = ttk.Button(query_frame, text="execute", command=self.execute_query)
        query_buttton.pack(side="left")

        query_frame.pack(fill="x")

        ttk.Label(text="Query result here:").pack()

        # query result field
        self.query_result_field = ScrolledText(self, relief=tk.GROOVE, wrap=tk.NONE, foreground="lime")
        self.query_result_field.pack(expand=True, fill="both")
        horizontal_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.query_result_field.xview)
        horizontal_scrollbar.pack(fill="x")
        self.query_result_field.config(xscrollcommand=horizontal_scrollbar.set, bg="black")

        self.events_view = tk.Listbox(self)
        self.events_view.pack(fill="x")
        self.insert_event_to_list("info", "Welcome to simple sqlite query manager!")
        #============================================================================================= UI

    def insert_event_to_list(self, event_state: Literal["success", "info", "error"], message: str):
        """
        Inserts event message to events list.

        Prameters:
        ------------
        event_state: current event state
        message: event's text message
        """
        EventConfig = namedtuple("EventConfig", ["color", "header"]) # config model
        config = () # result message config (text color, text header)

        match event_state:
            case "success": # success state
                config = EventConfig(color="green", header="-[Success]: ")
            case "info": # info state
                config = EventConfig(color=None, header="-[Info]: ")
            case "error": # error state
                config = EventConfig(color="red", header="-[Error]: ")

        # format and insert message to list
        items_count = self.events_view.size()
        current_time = time.strftime("%H:%M:%S", time.localtime()) # get time now
        event_message = f"[{current_time}]{config.header}" + message
        self.events_view.insert(items_count, event_message)
        self.events_view.see(tk.END) # scroll down

        # set color to message text
        if config.color is not None:
            self.events_view.itemconfig(items_count, fg=config.color)

    def clear_query_output_field(self): 
        """Clears query result field."""
        self.query_result_field.delete("1.0", "end") #clearing the query result field

    def pick_db_file(self):
        """Picks db file path with the filedialog."""
        db_path = filedialog.askopenfilename(
            title="Select DB file", 
            filetypes=[("DB file", "*.db"), ("All files", "*.")]
        )

        if os.path.exists(db_path):
            self.selected_db.set(db_path)
            self.insert_event_to_list("info", f"{db_path} db selected.")
        else: 
            self.insert_event_to_list("error", "Db path is not exists!")

    @async_handler
    async def execute_query(self):
        """Executes user query."""
        path_to_db = self.selected_db.get()
        if os.path.exists(path_to_db):
            self.clear_query_output_field() # clear output field for new result
            query_result = self.sqlite_db_manager.execute_query(
                self.selected_db.get(), 
                self.user_query.get()
            ) # get query result

            if query_result.data is not None:
                self.query_result_field.insert("1.0", query_result.data)
                self.insert_event_to_list("success", f"Query [{self.user_query.get()}] executed succesfully!")
            else:
                self.insert_event_to_list("error", query_result.exception_message)
        else:
            messagebox.showerror("Error", "Path to db is not exists or not selected!")
            self.insert_event_to_list("error", "Path to db is not exists or not selected!")

if __name__ == "__main__":
    sqliteQueryManagerApp = SqliteQueryManagerApp()
    async_mainloop(sqliteQueryManagerApp) # launch main async loop