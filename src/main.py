from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth.auth_routes import auth_router
from routes.agent.agent_routes import agent_router
from routes.ai_model.ai_model_routes import ai_model_router

app = FastAPI(
    title="GiTeams API",
    version="0.1.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(ai_model_router)


@app.get("/")
async def root():
    return {"message": "O que se tá fazendo aqui? 🥸"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
