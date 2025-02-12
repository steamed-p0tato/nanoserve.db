from flask import Flask, request, jsonify, g
from functools import wraps
import glob
import os
import sqlite3
from typing import Dict, List, Any
import os

app = Flask(__name__)

# Configuration
DATABASE = 'database.db'  # Default database
DATABASE_DIR = '.'  # Directory to store databases
CURRENT_DB = None  # Will store the current active database
TABLE_NAME = 'items'  # You can change this to match your table name
API_KEY = 'your-secret-api-key-here'  # Change this to a secure key

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')
        if provided_key and provided_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({'error': 'Invalid or missing API key'}), 401
    return decorated_function

def get_current_db():
    """Get the current active database name"""
    global CURRENT_DB
    return CURRENT_DB if CURRENT_DB else DATABASE

def set_current_db(db_name):
    """Set the current active database"""
    global CURRENT_DB
    CURRENT_DB = db_name

def get_db(db_name=None):
    """Get database connection"""
    if db_name is None:
        db_name = get_current_db()
    
    # Ensure the database name ends with .db
    if not db_name.endswith('.db'):
        db_name += '.db'
    
    db_path = os.path.join(DATABASE_DIR, db_name)
    
    # Get or create connection for this database
    connections = getattr(g, '_databases', {})
    if db_path not in connections:
        connections[db_path] = sqlite3.connect(db_path)
        connections[db_path].row_factory = sqlite3.Row
        g._databases = connections
    return connections[db_path]

@app.teardown_appcontext
def close_connections(exception):
    """Close all database connections at the end of request"""
    connections = getattr(g, '_databases', {})
    for db in connections.values():
        db.close()
    g._databases = {}

def init_db(db_name=None):
    """Initialize the database and create table if it doesn't exist"""
    with app.app_context():
        db = get_db(db_name)
        cursor = db.cursor()
        
        # Create a sample table if it doesn't exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Database management routes
@app.route('/api/databases', methods=['GET'])
@require_api_key
def list_databases():
    """List all databases in the directory"""
    try:
        # Get all .db files in the directory
        db_files = glob.glob(os.path.join(DATABASE_DIR, '*.db'))
        databases = [os.path.basename(db) for db in db_files]
        return jsonify({
            'databases': databases,
            'current_database': os.path.basename(get_current_db())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/databases/<string:db_name>', methods=['DELETE'])
@require_api_key
def delete_database(db_name):
    """Delete a database"""
    try:
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        db_path = os.path.join(DATABASE_DIR, db_name)
        
        # Check if database exists
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
            
        # Check if it's the current database
        if db_name == os.path.basename(get_current_db()):
            return jsonify({'error': 'Cannot delete current active database'}), 400
        
        # Close any existing connections
        connections = getattr(g, '_databases', {})
        if db_path in connections:
            connections[db_path].close()
            del connections[db_path]
        
        # Delete the file
        os.remove(db_path)
        
        return jsonify({'message': f'Database {db_name} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/databases/switch', methods=['POST'])
@require_api_key
def switch_database():
    """Switch the current active database"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Database name is required'}), 400
        
        db_name = data['name']
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        db_path = os.path.join(DATABASE_DIR, db_name)
        
        # Check if database exists
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        # Set as current database
        set_current_db(db_name)
        
        return jsonify({
            'message': f'Switched to database {db_name}',
            'current_database': db_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/databases', methods=['POST'])
@require_api_key
def create_database():
    """Create a new database"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Database name is required'}), 400
        
        db_name = data['name']
        if not db_name.endswith('.db'):
            db_name += '.db'
            
        db_path = os.path.join(DATABASE_DIR, db_name)
        
        # Check if database already exists
        if os.path.exists(db_path):
            return jsonify({'error': 'Database already exists'}), 400
            
        # Initialize the new database with the default table
        init_db(db_name)
        
        return jsonify({
            'message': f'Database {db_name} created successfully',
            'database': db_name
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CRUD Routes

@app.route('/api/items', methods=['GET'])
@require_api_key
def get_items():
    """Get all items"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM {TABLE_NAME}')
        items = cursor.fetchall()
        
        # Convert items to list of dicts
        return jsonify([dict(item) for item in items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['GET'])
@require_api_key
def get_item(item_id: int):
    """Get a single item by ID"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id = ?', (item_id,))
        item = cursor.fetchone()
        
        if item is None:
            return jsonify({'error': 'Item not found'}), 404
            
        return jsonify(dict(item))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items', methods=['POST'])
@require_api_key
def create_item():
    """Create a new item"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            f'INSERT INTO {TABLE_NAME} (name, description) VALUES (?, ?)',
            (data['name'], data.get('description'))
        )
        db.commit()
        
        return jsonify({
            'id': cursor.lastrowid,
            'name': data['name'],
            'description': data.get('description')
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
@require_api_key
def update_item(item_id: int):
    """Update an existing item"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Check if item exists
        cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id = ?', (item_id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Item not found'}), 404
            
        # Update the item
        update_fields = []
        values = []
        if 'name' in data:
            update_fields.append('name = ?')
            values.append(data['name'])
        if 'description' in data:
            update_fields.append('description = ?')
            values.append(data['description'])
            
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
            
        values.append(item_id)
        query = f'UPDATE {TABLE_NAME} SET {", ".join(update_fields)} WHERE id = ?'
        cursor.execute(query, values)
        db.commit()
        
        # Get updated item
        cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id = ?', (item_id,))
        updated_item = cursor.fetchone()
        
        return jsonify(dict(updated_item))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_item(item_id: int):
    """Delete an item"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if item exists
        cursor.execute(f'SELECT * FROM {TABLE_NAME} WHERE id = ?', (item_id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Item not found'}), 404
            
        cursor.execute(f'DELETE FROM {TABLE_NAME} WHERE id = ?', (item_id,))
        db.commit()
        
        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    app.run(debug=True)