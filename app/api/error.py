from werkzeug.http import HTTP_STATUS_CODES


def error_response(status_code, message=None):
    """Also plagiarized from Miguel Ginberg's guide:
    github.com/miguelgrinberg/microblog/
    """
    payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
    if message:
        payload["message"] = message
    return payload, status_code