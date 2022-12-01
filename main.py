import os, sys, copy, socket, threading, time, hashlib, configparser, datetime, pymssql, json, csv, math

from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')  # Disables touch_interface hold binding to rightclick
# Window.size = (1366, 600)
Window.maximize()

KV = '''
WindowManager:

    MDScreen:
        name: "Screen 1"
        MDBoxLayout:
            orientation: "vertical"
            MDBoxLayout:
                orientation: "horizontal"
                padding: "56dp"
                spacing: "24dp"

                MDBoxLayout:
                    orientation: "vertical"
                    MDLabel:
                        bold: True
                        text: "Rush Orders"
                        halign: 'center'
                        size_hint_max_y: "35dp"
                        # color: (1,0.5,0,1)
                        md_bg_color: (1,0.5,0,1)
                    RushOrders:
                        id: rush_table_screen
                        size_hint_max: (None,None)
                
                MDBoxLayout:
                    orientation: "vertical"
                    MDLabel:
                        bold: True
                        text: "Regular Orders"
                        halign: 'center'
                        size_hint_max_y: "35dp"
                        md_bg_color: (0,0.5,1,1)
                    RegularOrders:
                        id: normal_table_screen
                        size_hint_max: (None,None)
        
            # MDRaisedButton:
            #     text: "DELETE CHECKED ROWS"
            #     on_release: table_screen.delete_checked_rows()
'''

def establish_conn_db():  # connects sql, returns the remote connector
    server = 'bi-sql3.bitsinc.com'
    database = 'NSPG'
    username = 'StatusChanger'
    password = '***************'
    try:
        cnxn = pymssql.connect(server, username, password, database)
        return cnxn
    except Exception as e:
        print(e)
        return e

def query(table, filter):
    conn = establish_conn_db()
    sel = conn.cursor()
    sel.execute(f"select * from {table} where {filter};")
    row = sel.fetchall()
    conn.close()
    return row

class WindowManager(MDScreenManager):
    pass


class RushOrders(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.data_tables = MDDataTable(
            background_color_cell='#262626',
            background_color_selected_cell='#262626',
            use_pagination=True,
            check=False,
            rows_num=14,
            column_data=[
                ("Sales Order", dp(30)),
                ("Customer", dp(70)),
                ("Quantity", dp(15)),
                ("Days in Progress", dp(15)),
                ("In Date", dp(30)),
            ]
        )
        self.data_tables.row_data = self.data
        self.add_widget(self.data_tables)
        Clock.schedule_interval(self.get_data, 5)

    def get_data(self, dt):
        this = query("Orders", "(status = 1 or status = 0) and lab_notes like '%Rush Order%'")
        self.data = []
        try:
            for e in this:
                stat_log = json.loads(e[2])
                in_date = stat_log[0]['time']
                try:
                    in_days = datetime.datetime.strptime(in_date, '%Y-%m-%d %H:%M') - datetime.datetime.today()
                except Exception as ex:
                    print(ex)
                    in_days = 0
                
                # print(in_date)
                # print(out_date)
                so = e[0]
                cus = e[5]
                qty = e[15]

                values = [[so, cus, qty, -in_days.days, in_date]]
                self.data += values
            self.data.sort(key=lambda x: x[3], reverse=True)
                
        except Exception as e:
            print(f'{e}')
        self.change_color_days(self)

    def change_color_days(self, dt):
        try:
            data = copy.deepcopy(self.data)
            for i in range(len(data)):
                if int(data[i][3]) >= 2:
                    print(f"SO#: {self.data[i][0]}\nDays In Progress: {self.data[i][3]}")
                    for t in range(len(data[i])):
                        print(f"Setting {self.data[i][t]} on row {i} to Red")
                        data[i][t] = f"[color=#ff0000]{data[i][t]}[/color]"
                    print("\n")
                    continue
                if int(data[i][3]) >= 1:
                    print(f"SO#: {self.data[i][0]}\nDays In Progress: {self.data[i][3]}")
                    for t in range(len(data[i])):
                        print(f"Setting {self.data[i][t]} on row {i} to Orange")
                        data[i][t] = f"[color=#ff9d00]{data[i][t]}[/color]"
                    print("\n")
                    continue
            self.data_tables.update_row_data(self.data, data)

        except Exception as e:
            print(e)

    def cycle_orders(self, dt):
        try:
            self.pagemax = math.ceil(len(self.data) / 14)
        except Exception as ex:
            print(ex)
        if self.page >= 0 and self.page != self.pagemax:
            for _ in range(self.page):
                self.data_tables.table_data.set_next_row_data_parts("forward")
            self.page += 1
        else:
            try:
                for _ in range(self.page):
                    self.data_tables.table_data.set_next_row_data_parts("backward")
                    self.page = 0
            except Exception as ex:
                print(f"No page to return to")

class RegularOrders(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.page = 0
        self.pagemax = 0
        self.data_tables = MDDataTable(
            background_color_cell='#262626',
            background_color_selected_cell='#262626',
            use_pagination=True,
            check=False,
            rows_num=14,
            column_data=[
                ("Sales Order", dp(30)),
                ("Customer", dp(70)),
                ("Quantity", dp(15)),
                ("Days in Progress", dp(15)),
                ("In Date", dp(30)),
            ]
        )
        self.data_tables.row_data = self.data
        self.add_widget(self.data_tables)
        Clock.schedule_interval(self.get_data, 5)

    def get_data(self, dt):
        #print(self.data_tables.row_data)
        this = query("Orders", "(status = 1 or status = 0)")
        self.data = []
        try:
            for e in this:
                stat_log = json.loads(e[2])
                in_date = stat_log[0]['time']
                try:
                    in_days = datetime.datetime.strptime(in_date, '%Y-%m-%d %H:%M') - datetime.datetime.today()
                except Exception as ex:
                    print(ex)
                    in_days = 0
                
                # print(in_date)
                # print(out_date)
                so = e[0]
                cus = e[5]
                qty = e[15]

                values = [[so, cus, qty, -in_days.days, in_date]]
                self.data += values
            self.data.sort(key=lambda x: x[3], reverse=True)
                
        except Exception as e:
            print(f'{e}')
        self.change_color_days(self)
        self.cycle_orders(self)

    def change_color_days(self, dt):
        try:
            data = copy.deepcopy(self.data)
            for i in range(len(data)):
                if int(data[i][3]) >= 3:
                    # print(f"SO#: {self.data[i][0]}\nDays In Progress: {self.data[i][3]}")
                    for t in range(len(data[i])):
                        # print(f"Setting {self.data[i][t]} on row {i} to Red")
                        data[i][t] = f"[color=#ff0000]{data[i][t]}[/color]"
                    # print("\n")
                    continue
                if int(data[i][3]) >= 2:
                    # print(f"SO#: {self.data[i][0]}\nDays In Progress: {self.data[i][3]}")
                    for t in range(len(data[i])):
                        # print(f"Setting {self.data[i][t]} on row {i} to Orange")
                        data[i][t] = f"[color=#ff9d00]{data[i][t]}[/color]"
                    # print("\n")
                    continue
            self.data_tables.update_row_data(self.data, data)

        except Exception as e:
            print(e)
    
    def cycle_orders(self, dt):
        try:
            self.pagemax = math.ceil(len(self.data) / 14)
        except Exception as ex:
            print(ex)
        if self.page >= 0 and self.page != self.pagemax:
            for _ in range(self.page):
                self.data_tables.table_data.set_next_row_data_parts("forward")
            self.page += 1
        else:
            try:
                for _ in range(self.page):
                    self.data_tables.table_data.set_next_row_data_parts("backward")
                    self.page = 0
            except Exception as ex:
                print(f"No page to return to")


class DashboardApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Red"
        return Builder.load_string(KV)


DashboardApp().run()
