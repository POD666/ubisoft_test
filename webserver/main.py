import fernet
import base64
from aiohttp import web
from aiohttp_session import setup, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from routes import setup_routes
from tasks import start_background_tasks, cleanup_background_tasks


# secret_key must be 32 url-safe base64-encoded bytes
fernet_key = fernet.Fernet.generate_key()
secret_key = base64.urlsafe_b64decode(fernet_key)

app = web.Application()
setup(app, EncryptedCookieStorage(secret_key))

setup_routes(app)

app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)

web.run_app(app, host='127.0.0.1', port=8080)
