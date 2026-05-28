from paas_web_app.app import create_app, run

app = create_app()

__all__ = ["app", "run"]

if __name__ == '__main__':
    run()
