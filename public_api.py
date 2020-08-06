import tornado.web
import tornado.log
import tornado.options
import logging
import json
from tornado.httpclient import AsyncHTTPClient, HTTPClient
from tornado.httputil import url_concat
from tornado.escape import json_encode
from urllib.parse import urlencode


class App(tornado.web.Application):
    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)


class BaseHandler(tornado.web.RequestHandler):
    LISTING_API = "http://localhost:6000/listings"
    USER_API = "http://localhost:6001/users"

    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))


# /public-api/listings
class ListingsApiHandler(BaseHandler):
    async def get(self):
        try:
            # Get params
            page_num = self.get_argument("page_num", 1)
            page_size = self.get_argument("page_size", 10)
            user_id = self.get_argument("user_id", None)

            params = {"page_num": page_num, "page_size": page_size}
            if user_id:
                params["user_id"] = user_id

            # Get all listings (with user_id param - optional)
            listing_url = url_concat(self.LISTING_API, params)
            listings_response = await AsyncHTTPClient().fetch(
                listing_url,
                method='GET',
            )
            listings_dict = json.loads(listings_response.body)

            if listings_dict["result"] is False:
                self.write_json({
                    "result": False,
                    "errors": listing_dict["errors"],
                }, status_code=400)
                return

            # Combine results
            listings = []
            fields = ["id", "listing_type",
                      "price", "created_at", "updated_at"]
            user_memo = {}
            for row in listings_dict["listings"]:
                listing = {field: row[field] for field in fields}
                # Get user by id
                # Assume all user_ids in listings are valid
                user_dict = {}
                user_id = row["user_id"]
                # Reduce repetitive API calls with memo
                if user_id in user_memo:
                    user_dict["user"] = user_memo[user_id]
                else:
                    user_url = "%s/%s" % (self.USER_API, user_id)
                    user_response = await AsyncHTTPClient().fetch(user_url, method='GET')
                    user_dict = json.loads(user_response.body)
                    user_memo[user_id] = user_dict["user"]

                listing["user"] = user_dict["user"]
                listings.append(listing)
            self.write_json({"result": True, "listings": listings})
        except Exception as e:
            error_message = "Error while getting listings: %s" % str(e)
            logging.exception(error_message)
            self.write_json({
                "result": False,
                "errors": error_message
            }, status_code=400)

    async def post(self):
        # Convert JSON to Form params
        data = json.loads(self.request.body.decode("utf-8"))
        body = urlencode(data)
        try:
            listings_response = await AsyncHTTPClient().fetch(
                self.LISTING_API,
                method='POST',
                body=body,
            )
            listings_dict = json.loads(listings_response.body)
            if listings_dict["result"] is False:
                self.write_json({
                    "result": False,
                    "errors": listings_dict["errors"],
                }, status_code=400)
                return

            self.write_json({
                "listing": listings_dict["listing"]
            }, status_code=200)
        except Exception as e:
            error_message = "Error while creating listing: %s" % str(e)
            logging.exception(error_message)
            self.write_json({
                "result": False,
                "errors": error_message
            }, status_code=400)


# /public-api/users
class UsersApiHandler(BaseHandler):
    async def post(self):
        # Convert JSON to Form params
        data = json.loads(self.request.body.decode("utf-8"))
        body = urlencode(data)
        try:
            users_response = await AsyncHTTPClient().fetch(
                self.USER_API,
                method='POST',
                body=body
            )
            users_dict = json.loads(users_response.body)
            if users_dict["result"] is False:
                self.write_json({
                    "result": False,
                    "errors": users_dict["errors"],
                }, status_code=400)
                return

            self.write_json({"user": users_dict["user"]}, status_code=200)
        except Exception as e:
            error_message = "Error while creating user: %s" % str(e)
            logging.exception(error_message)
            self.write_json({
                "result": False,
                "errors": error_message,
            }, status_code=400)


def make_app(options):
    return App([
        (r"/public-api/listings", ListingsApiHandler),
        (r"/public-api/users", UsersApiHandler),
    ], debug=options.debug)


if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6002)
    tornado.options.define("port", default=6002)
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
    logging.info("Starting public APIs. PORT: {}, DEBUG: {}".format(
        options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()
