from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
import json
from datetime import date, datetime
from typing import Optional, Dict, Any, List

# Mevcut modüllerinizi import edin
import api_utils
import analysis_logic
import elo_utils

app = FastAPI(title="Güvenilir Analiz", description="Futbol Analiz Platformu")

# Static files ve templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# Session store (basit in-memory, production'da Redis kullanın)
sessions = {}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Kullanıcı authentication"""
    # Mevcut config.yaml sisteminizi kullanın
    import yaml
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        users = config.get('credentials', {}).get('usernames', {})
        user = users.get(credentials.username)
        
        if user and user.get('password') == credentials.password:
            return credentials.username
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = Depends(get_current_user)):
    """Ana sayfa"""
    # Kullanıcı bilgilerini al
    user_info = api_utils.get_user_usage_info(username)
    
    # Günün maçlarını al (sistem API)
    today_fixtures = []
    try:
        fixtures, _ = api_utils.get_fixtures_by_date(
            os.environ.get('API_KEY'), 
            "https://v3.football.api-sports.io",
            [39, 140, 203],  # Premier, La Liga, Süper Lig
            date.today(),
            bypass_limit_check=True
        )
        today_fixtures = fixtures[:10] if fixtures else []
    except Exception as e:
        print(f"Fixture alım hatası: {e}")
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "username": username,
        "user_info": user_info,
        "fixtures": today_fixtures
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(get_current_user)):
    """Maç panosu"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username
    })

@app.post("/api/analyze")
async def analyze_match(
    home_team: str = Form(...),
    away_team: str = Form(...),
    username: str = Depends(get_current_user)
):
    """Maç analizi API endpoint"""
    try:
        # API kullanım kontrolü
        if not api_utils.check_api_usage_limit(username):
            raise HTTPException(status_code=429, detail="API limiti aşıldı")
        
        # Takım bilgilerini al
        home_data = api_utils.get_team_id(
            os.environ.get('API_KEY'),
            "https://v3.football.api-sports.io", 
            home_team
        )
        away_data = api_utils.get_team_id(
            os.environ.get('API_KEY'),
            "https://v3.football.api-sports.io", 
            away_team
        )
        
        if not home_data or not away_data:
            raise HTTPException(status_code=404, detail="Takım bulunamadı")
        
        # Analiz yap (mevcut mantığınızı kullanın)
        # ... analiz kodu ...
        
        result = {
            "success": True,
            "home_team": home_data['name'],
            "away_team": away_data['name'],
            "prediction": "1X2 tahmini burada olacak",
            "confidence": 85
        }
        
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fixtures")
async def get_fixtures(
    date_str: str,
    leagues: str,
    username: str = Depends(get_current_user)
):
    """Maç listesi API"""
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        league_ids = [int(x) for x in leagues.split(',')]
        
        fixtures, error = api_utils.get_fixtures_by_date(
            os.environ.get('API_KEY'),
            "https://v3.football.api-sports.io",
            league_ids,
            selected_date,
            bypass_limit_check=True
        )
        
        if error:
            raise HTTPException(status_code=500, detail=error)
            
        return JSONResponse({"fixtures": fixtures or []})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))