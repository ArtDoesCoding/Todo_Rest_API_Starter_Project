from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, ValidationError
import os

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'todos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    completed = db.Column(db.Boolean, default=False)


class TodoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Todo
        load_instance = True
        sqla_session = db.session

    id = ma.auto_field()
    title = fields.String(required=True)
    completed = ma.auto_field()


todo_schema = TodoSchema()
todos_schema = TodoSchema(many=True)


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify(error.messages), 400


@app.route('/')
def home():
    return "Welcome to the To-Do List API!"


@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    result = todos_schema.dump(todos)
    return jsonify(result)


@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    try:
        new_todo = todo_schema.load(data, session=db.session)
        db.session.add(new_todo)
        db.session.commit()
        result = todo_schema.dump(new_todo)
        return jsonify(result), 201
    except ValidationError as e:
        return jsonify(e.messages), 400


@app.route('/todos/<int:id>', methods=['GET'])
def get_todo_by_id(id):
    todo = Todo.query.get_or_404(id)
    result = todo_schema.dump(todo)
    return jsonify(result)


@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo_by_id(id):
    todo = Todo.query.get_or_404(id)
    data = request.get_json()
    try:
        updated_todo = todo_schema.load(data, instance=todo, session=db.session)
        db.session.commit()
        result = todo_schema.dump(updated_todo)
        return jsonify(result)
    except ValidationError as e:
        return jsonify(e.messages), 400


@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo_by_id(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return '', 204


def init_db():
    """Initialize the database."""
    os.makedirs(app.instance_path, exist_ok=True)
    print("Checking if database file exists...")
    db_path = os.path.join(app.instance_path, 'todos.db')
    if not os.path.exists(db_path):
        print(f"Database file does not exist at {db_path}. Creating database tables...")
    else:
        print(f"Database file already exists at {db_path}.")

    try:
        print("Creating tables if not exist...")
        db.create_all()
        print("Tables checked/created.")
    except Exception as e:
        print(f"Error during table creation: {e}")

    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables in the database: {tables}")

    if 'todo' in tables:
        print("Table 'todo' exists.")
    else:
        print("Table 'todo' does not exist.")


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
