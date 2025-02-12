# Do install Flask
```bash
pip install flask
```
# Run the app
```bash
python3 server.py
```
### Otther requirements which are already built in
```txt
Flask==3.0.0
Werkzeug==3.0.1
click==8.1.7
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3
```


# CRUD in a DB

### create a database with structure

```bash
curl -X POST http://localhost:5000/api/databases \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"name": "new_database"}'
  ```
  
### list content inside the databse
```bash
curl http://localhost:5000/api/items \
  -H "X-API-Key: your-secret-api-key-here"
  ```
  
### get specific item
```bash
curl http://localhost:5000/api/items/1 \
  -H "X-API-Key: your-secret-api-key-here"
```

### create new item
```bash
curl -X POST http://localhost:5000/api/items \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"name": "New Item", "description": "Description"}'
  ```
### update item
```bash
curl -X PUT http://localhost:5000/api/items/1 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"name": "Updated Item", "description": "New Description"}'
```
### delete  item
```bash
curl -X DELETE http://localhost:5000/api/items/1 \
  -H "X-API-Key: your-secret-api-key-here"
 ```
 
# Database Management

### list all databases
```bash
curl http://localhost:5000/api/databases \
  -H "X-API-Key: your-secret-api-key-here"
 ```
### delete database
```bash
curl -X DELETE http://localhost:5000/api/databases/database_name \
  -H "X-API-Key: your-secret-api-key-here"
  ```
### switch database
```bash
curl -X POST http://localhost:5000/api/databases/switch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-here" \
  -d '{"name": "database_name"}'
  ```
