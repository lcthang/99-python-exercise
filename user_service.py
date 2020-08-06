# Author: Le Cong Thang (Terence Le)

import tornado.web
import tornado.log
import tornado.options
import sqlite3
import logging
import json
import time


class App(tornado.web.Application):
    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

        # Initialising db connection
        self.db = sqlite3.connect("users.db")
        self.db.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cursor = self.db.cursor()

        # Create table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS 'users' (\
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
                name TEXT NOT NULL,\
                created_at INTEGER NOT NULL,\
                updated_at INTEGER NOT NULL\
            );"
        )
        self.db.commit()


class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))


# /users
class UsersHandler(BaseHandler):
    USER_FIELDS = ["id", "name", "created_at", "updated_at"]

    @tornado.gen.coroutine
    def get(self, user_id=None):
        # /users/{id}
        if user_id:
            cursor = self.application.db.cursor()
            results = cursor.execute("SELECT * FROM users WHERE id=%s" % user_id)

            for row in results:
                user = {field: row[field] for field in self.USER_FIELDS}
                self.write_json({"result": True, "user": user})
                return

            self.write_json({"result": False, "errors": "User not exist"})
        else:
            # Parsing params
            page_num = self.get_argument("page_num", 1)
            page_size = self.get_argument("page_size", 10)

            try:
                page_num = int(page_num)
                page_size = int(page_size)
                if page_num < 0 or page_size < 0:
                    self.write_json({
                        "result": False,
                        "errors": "Invalid negative value for page_num/page_size"
                    }, status_code=400)
                    return
            except Exception as e:
                error_message = "Error while parsing params: %s" % str(e)
                logging.exception(error_message)
                self.write_json({
                    "result": False,
                    "errors": error_message
                }, status_code=400)
                return

            # Build SELECT statement to fetch all users
            limit = page_size
            offset = (page_num - 1) * page_size
            cursor = self.application.db.cursor()
            results = cursor.execute(
                "SELECT * FROM users \
                ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            # Format return response
            users = []
            for row in results:
                user = {field: row[field] for field in self.USER_FIELDS}
                users.append(user)
            self.write_json({"result": True, "users": users})

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument("name")
        # Converting current time to microseconds
        time_now = int(time.time() * 1e6)

        # Store new user in db
        cursor = self.application.db.cursor()
        cursor.execute(
            "INSERT INTO 'users'\
            ('name', 'created_at', 'updated_at')\
            VALUES (?, ?, ?)",
            (name, time_now, time_now)
        )
        self.application.db.commit()

        # Error out if we fail to retrieve the newly created user
        if cursor.lastrowid is None:
            self.write_json({
                "result": False,
                "errors": "Error while adding user to db",
            }, status_code=500)
            return

        user = dict(
            id=cursor.lastrowid,
            name=name,
            created_at=time_now,
            updated_at=time_now,
        )
        self.write_json({"result": True, "user": user})


def make_app(options):
    return App([
        (r"/users", UsersHandler),
        (r"/users/([0-9]+)", UsersHandler),
    ], debug=options.debug)


if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6001)
    tornado.options.define("port", default=6001)
    # Specify whether the app should run in debug mode
    # Debug mode restarts the app automatically on file changes
    tornado.options.define("debug", default=True)

    # Read settings/options from command line
    tornado.options.parse_command_line()

    # Access the settings defined
    options = tornado.options.options

    # Create web app
    app = make_app(options)
    app.listen(options.port)
    logging.info("Starting user service. PORT: {}, DEBUG: {}".format(
        options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()
