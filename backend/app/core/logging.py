import logging
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("smart-task-manager")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [ReqID: %(request_id)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        
        # We attach the request_id to the logger via contextvars or just format it. 
        # For simplicity in async, we inject it into a dict that the formatter could use, 
        # or we just log directly inside the middleware.
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Extract user_id if token was parsed by auth middleware
            # (Note: AuthMiddleware runs after this one, so we might not have request.state.user here
            #  but we can log the path and status code)
            
            # Mask sensitive headers in logs if we wanted to dump them
            logger.info(
                f"Method={request.method} Path={request.url.path} Status={response.status_code} Duration={duration:.3f}s",
                extra={"request_id": request_id}
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Method={request.method} Path={request.url.path} Error={type(e).__name__} Duration={duration:.3f}s",
                extra={"request_id": request_id},
                exc_info=True
            )
            raise e
