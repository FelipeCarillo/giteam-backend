import json
from typing import Optional
from pydantic import BaseModel


class HttpRequest:
    def __init__(
            self,
            event: dict,
            body_base_model: Optional[BaseModel] = None,
            params_base_model: Optional[BaseModel] = None,
            headers_base_model: Optional[BaseModel] = None,
    ):
        self.body = event.get('body')
        self.headers = event.get('headers')
        self.params = event.get('queryStringParameters')

        self.body = json.loads(self.body) if isinstance(self.body, str) else cls.body
        self.body = self._build_base_model(body_base_model, self.body)

        self.headers = self._build_base_model(headers_base_model, self.headers)
        self.params = self._build_base_model(params_base_model, self.params)

    @staticmethod
    def _build_base_model(base_model: BaseModel, data: Optional[dict]):
        return base_model(**data) if base_model else data


class HttpResponse:
    @classmethod
    def ok(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For successful requests"""
        return cls._build_response(200, message, data, headers)

    @classmethod
    def created(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For successful creation requests"""
        return cls._build_response(201, message, data, headers)

    @classmethod
    def no_content(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For successful requests with no content"""
        return cls._build_response(204, message, data, headers)

    @classmethod
    def redirect(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For redirection requests"""
        return cls._build_response(302, message, data, headers)

    @classmethod
    def bad_request(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For bad requests"""
        return cls._build_response(400, message, data, headers)

    @classmethod
    def unauthorized(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For unauthorized requests, when the user is not authenticated or does not have permission"""
        return cls._build_response(401, message, data, headers)

    @classmethod
    def forbidden(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For forbidden requests, when the user does not have permission to access the resource"""
        return cls._build_response(403, message, data, headers)

    @classmethod
    def not_found(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For requests that tried to access a resource that does not exist"""
        return cls._build_response(404, message, data, headers)

    @classmethod
    def unprocessable_entity(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For requests with invalid data"""
        return cls._build_response(422, message, data, headers)

    @classmethod
    def internal_server_error(cls, message: str, data: Optional[dict] = None, headers: Optional[dict] = None):
        """For internal server exceptions"""
        return cls._build_response(500, message, data, headers)

    @staticmethod
    def _build_response(status_code: int, message: str, data: Optional[dict] = None,
                        headers: Optional[dict] = None):
        headers = headers or {}
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "message": message,
                "data": data
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
                **headers
            }
        }
