from fastapi import FastAPI

from src.modules.auth.auth_router import auth_router
from src.modules.home.home_router import home_router
from src.modules.agents.agents_router import agents_router

app = FastAPI(title="GiTeams API", version="0.1.0")

app.include_router(home_router)
app.include_router(auth_router)
app.include_router(agents_router)


@app.get("/")
async def root():
    return {"message": "O que se tá fazendo aqui? 🥸"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
