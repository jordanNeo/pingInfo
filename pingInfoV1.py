import subprocess
import sys
import platform
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import socket

# Check if running as a PyInstaller executable
is_pyinstaller = getattr(sys, 'frozen', False)

# If running as a PyInstaller executable, set the creationflags to hide the console
subprocess_args = {'creationflags': subprocess.CREATE_NO_WINDOW} if is_pyinstaller else {}


class PingConfigForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Ping Configuration")

        self.label_interval = ttk.Label(self, text="Interval between pings (seconds):")
        self.label_timeout_ms = ttk.Label(self, text="Timeout time (milliseconds):")
        self.label_size_bytes = ttk.Label(self, text="Ping size (bytes):")

        self.entry_interval = ttk.Entry(self)
        self.entry_timeout_ms = ttk.Entry(self)
        self.entry_size_bytes = ttk.Entry(self)

        # Set default values
        self.entry_interval.insert(0, self.parent.ping_config["interval"])  # Default ping interval
        self.entry_timeout_ms.insert(0, self.parent.ping_config["timeout_ms"])  # Default timeout time
        self.entry_size_bytes.insert(0, self.parent.ping_config["size_bytes"])  # Default ping size

        self.button_run = ttk.Button(self, text="Save Configuration", command=self.save_configuration)

        self.label_interval.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.label_timeout_ms.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.label_size_bytes.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.entry_interval.grid(row=0, column=1, padx=10, pady=5)
        self.entry_timeout_ms.grid(row=1, column=1, padx=10, pady=5)
        self.entry_size_bytes.grid(row=2, column=1, padx=10, pady=5)

        self.button_run.grid(row=3, column=0, columnspan=2, pady=10, padx=10)

    def save_configuration(self):
        interval = int(self.entry_interval.get())
        timeout_ms = int(self.entry_timeout_ms.get())
        size_bytes = int(self.entry_size_bytes.get())

        self.parent.ping_config["interval"] = interval
        self.parent.ping_config["timeout_ms"] = timeout_ms
        self.parent.ping_config["size_bytes"] = size_bytes
        self.destroy()

class PingToolApp(tk.Tk):
    def load_ip_addresses(self):
        try:
            with open("ip_addresses.txt", "r") as file:
                ip_addresses = file.read()
                self.text_ip_addresses.insert("1.0", ip_addresses)
        except FileNotFoundError:
            pass 

    def save_ip_addresses(self):
        ip_addresses = self.text_ip_addresses.get("1.0", "end-1c")  # Get the text content from the Text widget
        with open("ip_addresses.txt", "w") as file:
            file.write(ip_addresses)

    def on_closing(self):
        self.save_ip_addresses()
        self.destroy()

    def __init__(self):
        super().__init__()
        self.title("Ping Tool")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Style configuration
        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.map('Treeview', background=[('selected', 'light blue')], foreground=[('selected', 'black')])
        
        

        self.label_instruction = ttk.Label(self, text="Enter the list of IP addresses(seperated by space or line), set your configuration, then click 'Start Ping'")
        self.text_ip_addresses = tk.Text(self, height=5, width=40)
        self.button_open_form = ttk.Button(self, text="Open Ping Configuration", command=self.open_form)
        self.button_clear = ttk.Button(self, text="Refresh Ping Data", command=self.refresh_ping)
        self.button_start = ttk.Button(self, text="Start Ping", command=self.start_ping)
        self.button_stop = ttk.Button(self, text="Stop Ping", command=self.stop_ping)
        self.button_stop.state(["disabled"]) 

        # Create a table (Treeview widget) to display devices and their ping results
        self.result_table = ttk.Treeview(self, columns=("Datetime", "Reply IP", "TTL", "Status", "Ping Time"), show="tree headings")
        self.result_table.heading("#0", text="Device", anchor="w")
        self.result_table.column("#0", width="200", anchor="w")
        self.result_table.heading("#1", text="Date Time", anchor="center")
        self.result_table.column("#1", width="115", anchor="center")
        self.result_table.heading("#2", text="Reply IP", anchor="center")
        self.result_table.column("#2", width="200", anchor="center")
        self.result_table.heading("#3", text="TTL", anchor="center")
        self.result_table.column("#3", width="75", anchor="center")
        self.result_table.heading("#4", text="Status", anchor="center")
        self.result_table.column("#4", width="150", anchor="center")
        self.result_table.heading("#5", text="Ping Time", anchor="center")
        self.result_table.column("#5", width="75", anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.result_table.yview)
        self.result_table.configure(yscrollcommand=scrollbar.set)
        
        # Place the scrollbar and Treeview widgets in a grid
        scrollbar.grid(row=3, column=4, sticky="ns")
        self.result_table.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")

        self.result_table.tag_configure('Success', background='lightgreen')
        self.result_table.tag_configure('Failed', background='tomato2')
        self.result_table.tag_configure('Gray', background='lightblue')

        self.label_instruction.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        self.text_ip_addresses.grid(row=1, column=0, columnspan=4, padx=10, pady=5)
        self.button_open_form.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.button_clear.grid(row=4, column=1, padx=10, pady=5, sticky="e")
        self.button_start.grid(row=2, column=1, padx=5, pady=5, sticky="e")
        self.button_stop.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.result_table.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1, )

        self.load_ip_addresses()

        self.ping_config = {
            "ip_addresses": [],
            "interval": 30,  # Default ping interval (30 seconds)
            "timeout_ms": 1000,  # Default timeout time (1000 milliseconds)
            "size_bytes": 32  # Default ping size (32 bytes)
        }

        self.ping_data = {}  # Use a dictionary to store ping data by IP
        self.ping_timer_id = None
        self.ping_running = False

    def open_form(self):
        form = PingConfigForm(self)
        self.wait_window(form)

    def refresh_ping(self):
        self.result_table.delete(*self.result_table.get_children())
        self.ping_data.clear()

    def start_ping(self):
        if self.ping_running:
            return

        self.ping_running = True
        self.button_start.state(["disabled"]) 
        self.button_stop.state(["!disabled"]) 

        text = self.text_ip_addresses.get("1.0", "end-1c")
        ip_addresses = re.split(r'\n| ', text)
        interval = self.ping_config["interval"]
        timeout_ms = self.ping_config["timeout_ms"]
        size_bytes = self.ping_config["size_bytes"]

        state_dict = {}

        def traverse_top_level(tree, state_dict):
            top_level_items = tree.get_children("")
            if len(top_level_items)>0:
                for index, item in enumerate(top_level_items):
                    state_dict[index] = tree.item(item, 'open')

        def reopen_treeview(tree, state_dict):
            for index, state in state_dict.items():
                item = tree.get_children("")[index]
                if state:
                    tree.item(item, open=True)
                else:
                    tree.item(item, open=False)
        def handleBadHostname(ip_address):
            # Store the ping data in the dictionary under the
            # IP address key
            ping_data = [
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "Bad Hostname", ""]
                    ]
            if ip_address not in self.ping_data:
                self.ping_data[ip_address] = []
            self.ping_data[ip_address].extend(ping_data)

            # Clear the treeview
            self.result_table.delete(*self.result_table.get_children())


            # Add all the ping data to the treeview
            index =0
            for ip_address, data_list in self.ping_data.items():
                # Create a unique identifier for this IP's subtree
                if (index%2) == 0:
                    subtree_id = self.result_table.insert("", "end", text=ip_address)
                else:
                    subtree_id = self.result_table.insert("", "end", text=ip_address, tags = "Gray")
                
                index+=1
                fails = 0
                successes = 0

                # Add the ping data to the treeview under the IP's subtree
                for data in data_list:
                    if data[3] == "Success":
                        tag = "Success"
                        successes+=1
                    else:
                        tag = "Failed"
                        fails+=1
                    newItem = self.result_table.insert(subtree_id, "end", values=data,tags = tag)
                    parent_item = self.result_table.parent(newItem)
                    self.result_table.set(parent_item, 4, 'Timeouts: '+ str(fails))
                    self.result_table.set(parent_item, 3, 'Successes: '+ str(successes))
            



        def ping_devices():
            traverse_top_level(self.result_table,state_dict=state_dict)
            for ip_address in ip_addresses:
                ip_address = ip_address.strip()
                if not ip_address:
                    continue

                try:

                    system = platform.system()
                    if ":" in ip_address:
                        # IPv6 address
                        # Check for IPv6 format
                        try:
                            socket.inet_pton(socket.AF_INET6, ip_address)
                        except socket.error:
                            handleBadHostname(ip_address)
                            continue
                        command = self.get_ping_command(ip_address, system, timeout_ms, size_bytes, ipv6=True)
                    else:
                        # IPv4 address
                        # Check for IPv4 format
                        try:
                            socket.inet_pton(socket.AF_INET, ip_address)
                        except socket.error:
                            handleBadHostname(ip_address)
                            continue
                        command = self.get_ping_command(ip_address, system, timeout_ms, size_bytes, ipv6=False)



                    result = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        **subprocess_args  # Pass the creationflags argument here
                    )

                    lines = result.stdout.split('\n')

                    # Initialize a list for this IP's ping data
                    ping_data = []

                    for line in lines:
                        line = line.strip()
                        if "time=" in line:
                            # Continue with the rest of the processing
                            parts = line.split()
                            datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ip_match = re.search(r'\(\S+\)', line)
                            reply_ip = parts[2] if "from" in line else ""
                            ttl_match = re.search(r'TTL=\d+', line)
                            ttl = ttl_match.group(0)[4:] if ttl_match else ""
                            status = "Success"
                            ping_time_match = re.search(r'time=\d+', line)
                            ping_time = ping_time_match.group(0)[5:] if ping_time_match else ""
                            ping_data.append([datetime_now, reply_ip, ttl, status, ping_time])

                    # Store the ping data in the dictionary under the IP address key
                    if ip_address not in self.ping_data:
                        self.ping_data[ip_address] = []
                    self.ping_data[ip_address].extend(ping_data)

                    # Clear the treeview
                    self.result_table.delete(*self.result_table.get_children())

                    # Add all the ping data to the treeview
                    index = 0
                    for ip_address, data_list in self.ping_data.items():
                        successes = 0
                        fails = 0
                        # Create a unique identifier for this IP's subtree
                        if (index%2) == 0:
                            subtree_id = self.result_table.insert("", "end", text=ip_address)
                        
                        
                        else:
                            subtree_id = self.result_table.insert("", "end", text=ip_address, tags = "Gray")

                        index+=1
                            
                        # Add the ping data to the treeview under the IP's subtree
                        for data in data_list:
                            if data[3] == "Success":
                                tag = "Success"
                                successes +=1
                            else:
                                tag = "Failed"
                                fails+=1
                            
                            newItem = self.result_table.insert(subtree_id, "end", values=data, tags = tag)
                            parent_item = self.result_table.parent(newItem)
                            self.result_table.set(parent_item, 3, 'Successes: '+ str(successes))
                            self.result_table.set(parent_item, 4, 'Timeouts: '+ str(fails))

                except subprocess.CalledProcessError:
                    ping_data = [
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "Failed", "Timeout"]
                    ]

                    # Store the ping data in the dictionary under the
                    # IP address key
                    if ip_address not in self.ping_data:
                        self.ping_data[ip_address] = []
                    self.ping_data[ip_address].extend(ping_data)

                    # Clear the treeview
                    self.result_table.delete(*self.result_table.get_children())


                    # Add all the ping data to the treeview
                    index =0
                    for ip_address, data_list in self.ping_data.items():
                        # Create a unique identifier for this IP's subtree
                        if (index%2) == 0:
                            subtree_id = self.result_table.insert("", "end", text=ip_address)
                        else:
                            subtree_id = self.result_table.insert("", "end", text=ip_address, tags = "Gray")
                        
                        index+=1
                        fails = 0
                        successes = 0

                        # Add the ping data to the treeview under the IP's subtree
                        for data in data_list:
                            if data[3] == "Success":
                                tag = "Success"
                                successes+=1
                            else:
                                tag = "Failed"
                                fails+=1
                            newItem = self.result_table.insert(subtree_id, "end", values=data,tags = tag)
                            parent_item = self.result_table.parent(newItem)
                            self.result_table.set(parent_item, 4, 'Timeouts: '+ str(fails))
                            self.result_table.set(parent_item, 3, 'Successes: '+ str(successes))                            

            if self.ping_running:
                self.ping_timer_id = self.after(interval * 1000, ping_devices)

            reopen_treeview(self.result_table,state_dict)

        ping_devices()
        
        

    def stop_ping(self):
        if self.ping_running:
            self.ping_running = False
            self.button_stop.state(["disabled"]) 
            self.button_start.state(["!disabled"]) 
            if self.ping_timer_id:
                self.after_cancel(self.ping_timer_id)

    def get_ping_command(self, ip_address, system, timeout_ms, size_bytes, ipv6=False):
        command = []
        if system == "Windows":
            if ipv6:
                command = ["ping", "-6", "-n", "1", "-w", str(timeout_ms), "-l", str(size_bytes)]
            else:
                command = ["ping", "-n", "1", "-w", str(timeout_ms), "-l", str(size_bytes)]
        else:
            if ipv6:
                command = ["ping6", "-c", "1", "-W", str(timeout_ms / 1000), "-s", str(size_bytes)]
            else:
                command = ["ping", "-c", "1", "-W", str(timeout_ms / 1000), "-s", str(size_bytes)]
        command.append(ip_address)
        return command


if __name__ == "__main__":
    app = PingToolApp()
    app.tk.call("source", "azure.tcl")
    app.tk.call("set_theme", "light")
    app.mainloop()
