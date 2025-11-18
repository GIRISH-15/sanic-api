from sanic import Sanic
from sanic.response import text, json

app = Sanic("hello_api")


@app.get("/")
async def index(request):
    return text("Hello from Sanic+Docker+EC2, Checking enhancements dynamically,time delay!!!")


@app.get("/health")
async def health(request):
    return json({"status": "ok"})


if __name__ == "__main__":
    # single worker, no fancy options
    app.run(
        host="0.0.0.0",
        port=8000,
        workers=1,
        debug=False,
        access_log=True,
    )
