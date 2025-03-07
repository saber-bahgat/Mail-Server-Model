import socket
import threading
import sqlite3
import random
# Database Setup

def create_db():
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    
    # Create messages table
    cur.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        receiver TEXT,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Ensure 'is_read' column exists
    cur.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cur.fetchall()]
    if "is_read" not in columns:
        cur.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0;")
    
    conn.commit()
    conn.close()

create_db()

# Server Setup
HOST = "127.0.0.1"
PORT = random.randint(1026, 9999)
ADDR = (HOST, PORT)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(ADDR)
server_socket.listen()
clients = {}

def accept_connections():
    print("🚀 Server is running...")
    while True:
        client_socket, client_addr = server_socket.accept()
        print(f"✅ New connection from {client_addr}")
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

def private_message(sender, receiver, message, sender_socket):
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    if receiver in clients.values():
        for client_socket, username in clients.items():
            if username == receiver:
                try:
                    client_socket.send(f"[Private] {sender}: {message}".encode())
                except:
                    client_socket.close()
                    del clients[client_socket]
                return
    else:
        
        print(f"✅ Your message has been sent successfully to {receiver}.")
    cur.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, message))
    conn.commit()
    conn.close()

def handle_client(client_socket):
    client_socket.send("Enter your username: ".encode())
    username = client_socket.recv(1024).decode().strip()
    clients[client_socket] = username
    print(f"✅ {username} joined the chat!")
    client_socket.send("✅ Connected to the server!\n".encode())
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message.startswith("/private"):
                parts = message.split(" ", 2)
                if len(parts) >= 3:
                    _, receiver, private_msg = parts
                    private_message(username, receiver, private_msg, client_socket)
            else:
                print("Error404!, Please Try Ag")
        except:
            print(f"❌ {username} disconnected!")
            del clients[client_socket]
            client_socket.close()
            break

def inbox(username):
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    cur.execute("SELECT id, sender, message, timestamp FROM messages WHERE receiver = ? AND is_read = 0", (username,))
    messages = cur.fetchall()
    if not messages:
        print("📭 Inbox is empty!")
    else:
        print("-"*15)
        print("# Inbox!")
        for msg in messages:
            print(f"[{msg[0]}] From: @{msg[1]}\n   {msg[2]}  <Date: {msg[3]}>")
        msg_id = input("Enter message ID to read or 'exit' to go back: ")
        if msg_id.isdigit():
            cur.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (msg_id,))
            conn.commit()
    conn.close()

def change_username():
    global username  

    print("-" * 15)
    print("# Change Username!")
    new_user_name = input("Enter The New Username (0 to Return): ").strip()

    if new_user_name == username:
        print("The entered data is the same as before, Try modifying it!")
        return

    elif new_user_name == '0':
        print("Returned successfully...\n")
        return
    
    cur.execute("UPDATE users SET username = ? WHERE username = ?", (new_user_name, username))
    conn.commit()

    print(f"The Username: {username} >> {new_user_name}")
    username = new_user_name  
    print("-" * 15)

def change_password():
    global username  

    print("-" * 15)
    print("# Change Password!")

    attempts = 3
    while attempts > 0:
        check_passwd = input("Enter The Old Password: ").strip()
        
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        stored_passwd = cur.fetchone()

        if stored_passwd and check_passwd == stored_passwd[0]:  
            new_passwd = input("Enter The New Password: (0 To Return): ").strip()

            if new_passwd == check_passwd:
                print("The entered data is the same as before, Try modifying it!")
                continue

            elif new_passwd == '0':
                print("Returned successfully...\n")
                return
                
            cur.execute("UPDATE users SET password = ? WHERE username = ?", (new_passwd, username))
            conn.commit()

            print(f"The Password: '{check_passwd}' >> '{new_passwd}'")
            print("-" * 15)
            return
        
        else:
            attempts -= 1
            print(f"Incorrect password! {attempts} attempts left.")

    print("Too many failed attempts. Please try again later!")
    print("-" * 15)

def delete_account():
    global username  

    if "username" not in globals():  
        print("❌ You must be logged in to delete your account.")
        return False  

    print("-" * 15)
    print("# Delete Account!")

    attempts = 3
    while attempts > 0:
        confirm_passwd = input("Enter Your Password to Confirm Deletion: ").strip()

        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        stored_passwd = cur.fetchone()

        if stored_passwd and confirm_passwd == stored_passwd[0]:  
            confirm = input("⚠️ Are you sure? This action is irreversible! (Y/N): ").strip().lower()
            if confirm == 'y':
                cur.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                print("✅ Your account has been deleted successfully!")
                print("-" * 15)
                del username  
                return True  
            elif confirm == 'n':
                print("Account deletion canceled.")
                break  
            else:
                print("⚠️ Please enter 'Y' or 'N'.")
                continue
        
        else:
            attempts -= 1
            print(f"❌ Incorrect password! {attempts} attempts left.")

    print("🚫 Too many failed attempts. Please try again later!")
    print("-" * 15)
    return False  



def main_menu(username, client_socket):
    while True:
        print("\n📜 Main Menu:")
        print("1. Send Private Message")
        print("2. Send Public Message")
        print("3. Show Online Users")
        print("4. Inbox")
        print("5. Settings")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            print("-"*15)
            receiver = input("Enter recipient username: ").strip()
            message = input("Enter your message: ").strip()
            private_message(username, receiver, message, client_socket)
            print("-"*15)
        elif choice == "2":
            print("-"*15)
            print('Public Message - Coming Soon!')
            print("-"*15)
        elif choice == "3":
            print("-"*15)
            print("🟢 Online Users:")
            for user in clients.values():
                print(user)
            print("-"*15)
        elif choice == "4":
            inbox(username)
            print("-"*15)
        elif choice == "5":
            
            print("-"*15)
            print("# Settings!")
            print("[1] My Account")
            print("[2] Network Settings")
            print("[3] Return To Main Page")

            sett_choice = input("Enter Your Choice (1-3): ").strip()

            if sett_choice == '1':
                print("-"*15)
                print("# My Account!")
                print("[1] Display My Information")
                print("[2] Change Username")
                print("[3] Change Password")
                print("[4] Delete My Account")
                print("[5] Return To Main Page")

                acc_choice = input("Enter Your Choice (1-5): ").strip()
                if acc_choice == '1':
                    print("-"*15)
                    print("# Display My Information!")
                    print(f"Username: '{username}'")
                    print(f"Password: '{password}'")
                    print(f"Current Server IP: '{HOST}'")
                    print(f"Current Port Number: '{PORT}'")
                    print("-"*15)
                elif acc_choice == '2':
                    print("-"*15)
                    change_username()
                    print("-"*15)
                elif acc_choice == '3':
                    print("-"*15)
                    change_password()
                    print("-"*15)
                elif acc_choice == '4':
                    print("-"*15)
                    delete_account()
                    print("-"*15)
                elif acc_choice == '5':
                    print("Returned successfully...")
                    print("-"*15)
                else:
                    print("Invalid Choice!, Please Try Again...")
                    print("-"*15)
                    
            elif sett_choice == '2':
                print("-"*15)
                print('Network Settings - Coming Soon!')
                print("-"*15)
                    

            elif sett_choice == '3':
                    print("Returned successfully...")
                    print("-"*15)

        elif choice == "6":
            print("-"*15)
            print("👋 Logging out...")
            break
        else:
            print("⚠ Invalid choice! Try again.")

server_thread = threading.Thread(target=accept_connections, daemon=True)
server_thread.start()
while True:
    conn = sqlite3.connect("chat.db")
    cur = conn.cursor()
    choice = input("\n📌 Do you have an account? (Y/N): ").strip().lower()
    if choice == "y":
        username = input("👤 Enter your username: ").strip()
        password = input("🔑 Enter your password: ").strip()
        cur.execute("SELECT username, password FROM users WHERE username = ? AND password = ?", (username, password))
        user_data = cur.fetchone()
        if user_data:
            print(f"🎉 Login successful! Welcome, {username}")
            
            main_menu(username, None)
            break
        else:
            print("❌ User not found! Please register first.")
    elif choice == "n":
        username = input("📝 Enter a new username: ").strip()
        password = input("🔑 Enter your password: ").strip()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("✅ Account created successfully! You can now log in.")
    else:
        print("⚠ Please enter 'Y' or 'N'.")
    conn.close()
