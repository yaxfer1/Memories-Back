from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from bcrypt import hashpw, checkpw, gensalt
import embeder
import multiscraping
import jwt
import os
import dbManagement
app = Flask(__name__)
CORS(app)
JWT_SECRET = 'secret'
from introduccion import research_graph

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    print("ai_chat")
    try:
        # Obtener datos del JSON enviado en la solicitud
        data = request.get_json()

        # Extraer "id" y "message" asegurándonos de que existen
        chat_id = data.get("id")

        message = data.get("message")
        jwt_token = data.get('jwt')
        print(chat_id, message, jwt_token)
        try:
            payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=['HS256'])
            username = payload['iss']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        user_id = dbManagement.obtain_id_username(username)
        print(dbManagement.add_new_message(message, chat_id, user_id))
        # Validar que ambos datos sean correctos
        if chat_id is None or message is None:
            return jsonify({"error": "Missing 'id' or 'message'"}), 400
        print("response")
        # Llamar a la función que procesa el chat
        response = research_graph(str(message))
        print(response)
        dbManagement.add_new_aimessage(response, chat_id)
        return jsonify(response)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrap_url', methods=['POST'])
def scrap_url():
    print("scraping url")
    data = request.get_data()

    # Decodificar los bytes
    decoded_text = data.decode('utf-8')

    # Remover comillas adicionales
    normalized_text = decoded_text.strip('"')

    print(normalized_text)
    print(data)
    text = multiscraping.scrape_url(normalized_text)
    print(text)
    processor = embeder.URLProcessor()
    embeder.URLProcessor.process_text(processor, text, data)
    return jsonify({
        "message": "URL Procesada",
        "url" : normalized_text,
        "texto" : text,
    }), 200

@app.route('/api/upload_files', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    uploaded_files = request.files.getlist("files")
    file_names = []
    files = []
    discarded_files = []
    processor = embeder.PDFProcessor(batch_size=10)

    for file in uploaded_files:
        if file.filename == '':
            return jsonify({"error": "One of the files has no name"}), 400

        file_path = f"uploads/{file.filename}"

        if os.path.exists(file_path):
            # Si el archivo ya existe, se descarta
            discarded_files.append(file.filename)
            print(f"El archivo {file_path}, ya existe en la BD")

        else:
            print(f"Guardando el archivo: {file_path} ")
            file.save(file_path)
            file_names.append(file.filename)
            files.append(file)

        print("sigue el for ------------------ debug")

    if files:
        text = embeder.PDFProcessor.process_pdfs_and_insert(processor, files)
        print(f"Texto extraído de los archivos:\n{text}")

    return jsonify({
        "message": "Archivos procesados",
        "files_uploaded": file_names,
        "files_discarded": discarded_files
    }), 200



# Función para generar el token JWT
def generate_jwt(username):
    payload = {
        'iss': username,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Token expira en 1 hora
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Obtain hash from database
    user_data = dbManagement.obtain_username_password(username)
    stored_hash_with_salt = user_data.get("password_hash")

    # Verify password
    if stored_hash_with_salt and checkpw(password.encode('utf-8'), stored_hash_with_salt.encode('utf-8')):
        token = generate_jwt(username)
        return jsonify({'jwt': token}), 201
    else:
        return jsonify({'error': 'Invalid Credentials'}), 403

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({'error': 'No se proporcionaron datos'}), 400

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Credenciales incompletas'}), 400

    # Hashear la contraseña antes de almacenarla en la base de datos
    hashed_password = hashpw(password.encode('utf-8'), gensalt())

    return dbManagement.register_normal(username, hashed_password)

@app.route('/api/add_chat', methods=['POST'])
def add_chat():
    data = request.json
    print(data)
    jwt_token = data.get('jwt')
    chat_name = data.get('chat_name')

    # Verificar y parsear el token JWT
    try:
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=['HS256'])
        username = payload['iss']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    user_id = dbManagement.obtain_id_username(username)
    if user_id:

        return dbManagement.add_chat_db(chat_name, user_id)
    else:
        return jsonify({'error': 'Usuario no encontrado'}), 404

@app.route('/api/get_chats', methods=['POST'])
def get_chats():
    data = request.json
    print("data: ")
    print(data)
    jwt_token = data.get('jwt')

    # Verificar y parsear el token JWT
    try:
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=['HS256'])
        username = payload['iss']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    #user_id = dbManagement.obtain_id_username(username)
    if username:
        dbreturn = dbManagement.obtain_chats_from_user(username)
        print(dbreturn)
        return dbreturn
    else:
        return jsonify({'error': 'Usuario no encontrado'}), 404

@app.route('/api/get_chat_messages', methods=['POST'])
def get_chat_messages():
    data = request.json
    #user_id = dbManagement.obtain_id_username(username)
    if data:
        dbreturn = dbManagement.get_chat_messages(data)
        print(dbreturn)
        return dbreturn
    else:
        return jsonify({'error': 'Mala peticion'}), 404

if __name__ == '__main__':
    app.run(debug=True)