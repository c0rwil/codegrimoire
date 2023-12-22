import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.code_grimoire import CodeGrimoire  # Import your class
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
TOKEN = os.getenv("TOKEN")
app = FastAPI(title="CodeGrimoire")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def oauth_token(token= TOKEN):
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token
@app.get("/login")
async def login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=repo"
    )

@app.post("/callback")
async def callback(code: str):
    token_response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code': code}
    ).json()

    access_token = token_response.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    # Returning access token to the frontend (or client)
    return {"access_token": access_token}
@app.post("/analyze")
async def analyze_repos():
    token: str = TOKEN
    grimoire = CodeGrimoire(token)
    grimoire.analyze_repos()
    return grimoire.total_lines, grimoire.repos_languages

def run():
    uvicorn.run("src.api:app", host="localhost", port=8000, reload=True)