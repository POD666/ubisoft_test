import handlers


def setup_routes(app):
    app.router.add_route('*', '/', handlers.index)
