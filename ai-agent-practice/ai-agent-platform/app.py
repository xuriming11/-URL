from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import json
import sqlite3
import uuid

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json', 'py'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('agent_hub.db')
    cursor = conn.cursor()
    
    # 创建agents表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            model_id VARCHAR(50) DEFAULT 'qwen-plus',
            api_key VARCHAR(200),
            base_url VARCHAR(200),
            config TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建conversations表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            title VARCHAR(200),
            messages TEXT,
            token_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    ''')
    
    # 创建files表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename VARCHAR(255) NOT NULL,
            original_name VARCHAR(255),
            filepath VARCHAR(500) NOT NULL,
            filesize INTEGER,
            filetype VARCHAR(50),
            category VARCHAR(50),
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建usage_logs表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            conversation_id INTEGER,
            token_used INTEGER,
            response_time FLOAT,
            status VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    ''')
    
    # 默认Agent
    cursor.execute('SELECT * FROM agents WHERE name = ?', ('默认Agent',))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO agents (name, description, model_id, config) 
            VALUES (?, ?, ?, ?)
        ''', ('默认Agent', '系统默认的AI助手', 'qwen-plus', json.dumps({'temperature': 0.7})))
    
    conn.commit()
    conn.close()

init_db()

# 辅助函数
def get_db_connection():
    conn = sqlite3.connect('agent_hub.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 主页
@app.route('/')
def index():
    return render_template('index.html')

# === Agent API ===
@app.route('/api/agents', methods=['GET'])
def get_agents():
    conn = get_db_connection()
    agents = conn.execute('SELECT * FROM agents ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(agent) for agent in agents])

@app.route('/api/agents', methods=['POST'])
def create_agent():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO agents (name, description, model_id, api_key, base_url, config)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['name'], data.get('description', ''), data.get('model_id', 'qwen-plus'),
          data.get('api_key', ''), data.get('base_url', ''), json.dumps(data.get('config', {}))))
    conn.commit()
    agent_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': agent_id, 'name': data['name']})

@app.route('/api/agents/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    conn = get_db_connection()
    agent = conn.execute('SELECT * FROM agents WHERE id = ?', (agent_id,)).fetchone()
    conn.close()
    if agent:
        return jsonify(dict(agent))
    return jsonify({'error': 'Agent not found'}), 404

@app.route('/api/agents/<int:agent_id>', methods=['PUT'])
def update_agent(agent_id):
    data = request.json
    conn = get_db_connection()
    conn.execute('''
        UPDATE agents SET name = ?, description = ?, model_id = ?, api_key = ?, 
                         base_url = ?, config = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (data['name'], data.get('description', ''), data.get('model_id', 'qwen-plus'),
          data.get('api_key', ''), data.get('base_url', ''), json.dumps(data.get('config', {})), agent_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/agents/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# === 对话 API ===
@app.route('/api/chat/<int:agent_id>', methods=['POST'])
def chat(agent_id):
    data = request.json
    message = data['message']
    
    # 模拟AI响应
    mock_responses = [
        f"收到你的消息：'{message}'\n\n这是AI的回复内容。",
        f"关于 '{message}' 的信息：\n- 要点1\n- 要点2\n- 要点3",
        f"分析你的问题：{message}\n\n我的回答是基于最新的知识。"
    ]
    response_text = mock_responses[hash(message) % len(mock_responses)]
    
    conn = get_db_connection()
    
    # 获取或创建对话
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (agent_id, title, messages)
            VALUES (?, ?, ?)
        ''', (agent_id, message[:50], json.dumps([{'role': 'user', 'content': message}])))
        conversation_id = cursor.lastrowid
        conn.commit()
    else:
        # 更新现有对话
        conv = conn.execute('SELECT messages FROM conversations WHERE id = ?', (conversation_id,)).fetchone()
        if conv:
            messages = json.loads(conv['messages'])
            messages.append({'role': 'assistant', 'content': response_text})
            conn.execute('UPDATE conversations SET messages = ? WHERE id = ?', 
                        (json.dumps(messages), conversation_id))
            conn.commit()
    
    # 记录日志
    conn.execute('''
        INSERT INTO usage_logs (agent_id, conversation_id, token_used, status)
        VALUES (?, ?, ?, ?)
    ''', (agent_id, conversation_id, len(response_text), 'success'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'response': response_text,
        'conversation_id': conversation_id,
        'tokens': len(response_text)
    })

@app.route('/api/conversations/<int:agent_id>', methods=['GET'])
def get_conversations(agent_id):
    conn = get_db_connection()
    conversations = conn.execute('SELECT * FROM conversations WHERE agent_id = ? ORDER BY created_at DESC', 
                               (agent_id,)).fetchall()
    conn.close()
    return jsonify([dict(conv) for conv in conversations])

# === 文件 API ===
@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO files (filename, original_name, filepath, filesize, filetype, category)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_filename, file.filename, filepath, os.path.getsize(filepath), ext, request.form.get('category', 'general')))
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': 1,
            'filename': new_filename,
            'original_name': file.filename,
            'filepath': filepath,
            'filesize': os.path.getsize(filepath)
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/files', methods=['GET'])
def get_files():
    conn = get_db_connection()
    files = conn.execute('SELECT * FROM files ORDER BY uploaded_at DESC').fetchall()
    conn.close()
    return jsonify([dict(f) for f in files])

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    conn = get_db_connection()
    file = conn.execute('SELECT filepath FROM files WHERE id = ?', (file_id,)).fetchone()
    if file:
        try:
            os.remove(file['filepath'])
        except:
            pass
        conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/files/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    conn = get_db_connection()
    file = conn.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
    conn.close()
    if file:
        return send_from_directory(app.config['UPLOAD_FOLDER'], file['filename'], 
                                 download_name=file['original_name'])
    return jsonify({'error': 'File not found'}), 404

# === 统计 API ===
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    
    total_agents = conn.execute('SELECT COUNT(*) FROM agents').fetchone()[0]
    total_conversations = conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
    total_files = conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]
    total_tokens = conn.execute('SELECT COALESCE(SUM(token_used), 0) FROM usage_logs').fetchone()[0]
    
    recent_usage = conn.execute('''
        SELECT strftime('%Y-%m-%d', created_at) as date, COUNT(*) as count
        FROM usage_logs 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'total_agents': total_agents,
        'total_conversations': total_conversations,
        'total_files': total_files,
        'total_tokens': total_tokens,
        'recent_usage': [dict(r) for r in recent_usage]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
