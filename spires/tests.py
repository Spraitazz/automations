#
# HOW TO: use selenium-wire (https://github.com/wkeeling/selenium-wire)
#         to mock up response to selenium driver.get()
#

# Example: Mock a response
# You can use request.create_response() to send a custom reply back to the browser. No data will be sent to the remote server.


def interceptor(request):
    if request.url == "https://server.com/some/path":
        request.create_response(
            status_code=200,
            headers={"Content-Type": "text/html"},  # Optional headers dictionary
            body="<html>Hello World!</html>",  # Optional body
        )


driver.request_interceptor = interceptor
driver.get(...)

# Requests to https://server.com/some/path will have their responses mocked
