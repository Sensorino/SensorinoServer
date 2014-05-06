from flask import Flask, request
from flask.ext.restful import Resource, Api

app = Flask(__name__)
api = Api(app)


class Sensorino(Resource):
    def get(self, sid):
        return {todo_id: todos[todo_id]}

    def put(self, todo_id):
        todos[todo_id] = request.form['data']
        return {todo_id: todos[todo_id]}

api.add_resource(TodoSimple, '/<string:todo_id>')

if __name__ == '__main__':
    app.run(debug=True)

