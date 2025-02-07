from datetime import datetime, timedelta
from bcrypt import hashpw, checkpw, gensalt
import jwt
from flask import jsonify
import mysql.connector

# Configuración de la conexión a la base de datos
config = {
    'user': '',
    'password': '',
    'host': 'localhost',
    'database': ''
}

def obtain_id_username(username):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    query = "SELECT id FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_id = cursor.fetchone()
    cursor.close()
    connection.close()
    return user_id

# Método para obtener elementos de un usuario por su ID de usuario
def obtain_elements_from_user(user):
    user_id = obtain_id_username(user)
    if user_id is None:
        return []  # O maneja este caso de alguna otra manera

    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    query = "SELECT name, type FROM elements WHERE owner_id = %s"
    cursor.execute(query, (user_id['id'],))  # Pasa solo el valor del ID como parámetro
    results = cursor.fetchall()
    elements = [row[0] for row in results]
    types = [row[1] for row in results]
    print(types)
    cursor.close()
    connection.close()

    return elements, types

def obtain_username_password(username):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    query = "SELECT password_hash FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user_password = cursor.fetchone()
    print(user_password)
    cursor.close()
    connection.close()
    print(user_password)
    return user_password

def register_normal(user, hashed_password):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    # Insertar el nuevo usuario y su contraseña hasheada en la base de datos
    query = "INSERT INTO users (username, password_hash, permission) VALUES (%s, %s, 'normal')"
    try:
        cursor.execute(query, (user, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'message': 'Usuario registrado correctamente'}), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        return jsonify({'error': f'Error al registrar usuario: {err}'}), 500

def add_element_db(element, type, user_id):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    print(element)
    print(type)
    print(user_id)
    ids = user_id.__getitem__("id")
    print(ids)
    query = "INSERT INTO elements (name, type, owner_id) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (element, type, ids))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(element, type), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        print(err)
        return jsonify({'error': f'Error at inserting element: {err}'}), 500

def obtain_chats_from_user(user):
    user_id = obtain_id_username(user)
    if user_id is None:
        return []  # O maneja este caso de alguna otra manera

    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    query = "SELECT id, namestr FROM chats WHERE owner_id = %s"
    cursor.execute(query, (user_id['id'],))  # Pasa solo el valor del ID como parámetro
    results = cursor.fetchall()
    names = [row[1] for row in results]
    #created_at = [row[1] for row in results]
    print(f"names: {names}")
    id= [row[0] for row in results]
    print(f"ids: {id}")
    #print(f"created_at: {created_at}")
    cursor.close()
    connection.close()

    return jsonify(id, names), 201


def add_chat_db(chat_name, user_id):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    print(chat_name)
    print(user_id)
    ids = user_id.__getitem__("id")
    print(ids)
    created_at = datetime.now()
    print(created_at)
    query = "INSERT INTO chats (namestr, created_at, owner_id) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (chat_name, created_at, ids))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(chat_name, created_at), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        print(err)
        return jsonify({'error': f'Error at inserting chat: {err}'}), 500

def add_new_message(message, chat_id, user_id):
    print("add_new_message")

    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("created at:", created_at)
    print("message:", message)
    print("chat_id:", chat_id)
    print("user_id:", user_id)
    ids = user_id.__getitem__("id")
    query = """
        INSERT INTO messages (chat_id, content, user_id) 
        VALUES (%s, %s, %s)
    """
    try:
        print("Ejecutando consulta SQL...")
        cursor.execute(query, (chat_id, message, ids))
        connection.commit()
        print(f"Mensaje insertado con ID: {cursor.lastrowid}")  # ✅ Verificar si se insertó

        cursor.close()
        connection.close()
        return jsonify("hola"), 201
    except mysql.connector.Error as err:
        print("Error:", err)
        cursor.close()
        connection.close()
        return jsonify({'error': f'Error al insertar el mensaje: {err}'}), 500

def add_new_aimessage(message, chat_id):
    print("add_new_aimessage")
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    userid = 42

    created_at = datetime.now()
    print(created_at)
    query = "INSERT INTO messages (chat_id, content, user_id) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (chat_id, message, userid))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        print(err)
        return jsonify({'error': f'Error at inserting new message: {err}'}), 500

def get_chat_messages(chat_id):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    ids = chat_id.__getitem__("chat_id")
    print(ids)
    query = "SELECT content, user_id FROM messages WHERE chat_id = %s ORDER BY time_set ASC"
    try:
        print("entrando al cursor")
        cursor.execute(query, (int(ids),))
        print("saliendo del cursor")
        results = cursor.fetchall()
        print(results)
        content = [row["content"] for row in results]
        user_id = [row["user_id"] for row in results]
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(content, user_id), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        return jsonify({'error': f'Error at retrieving messages from chat: {err}'}), 500

def rm_element_db(element, type, user_id):
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)
    print(element)
    print(type)
    print(user_id)
    ids = user_id.__getitem__("id")
    print(ids)
    query = "DELETE FROM elements WHERE name = %s AND type = %s AND owner_id = %s"
    try:
        cursor.execute(query, (element, type, ids))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify(element, type), 201
    except mysql.connector.Error as err:
        cursor.close()
        connection.close()
        print(err)
        return jsonify({'error': f'Error at inserting element: {err}'}), 500
