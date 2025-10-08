# main.py
import os
import json
import uuid
import base64
import logging
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

current_dir = Path(__file__).parent            # -> .../backend/servers
project_root = current_dir.parent.parent       # -> .../Situated_Learning (project root)
sys.path.insert(0, str(project_root))
from urllib.parse import unquote
from backend.services.saml_utils import *
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
import httpx

from backend.services.redis_manager import RedisManager  

app = FastAPI()
# read envs for other config
Redirect_Link = os.getenv("REDIRECT_LINK")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

# create a global RedisManager instance (configured by envs by default)
redis_mgr = RedisManager()

# initialize redis on startup
@app.on_event("startup")
async def startup_event():
    # init redis connection (raises if cannot connect)
    await redis_mgr.init()


@app.on_event("shutdown")
async def shutdown_event():
    await redis_mgr.close()


@app.get("/sla/login")
def login():
    authn_request = create_authn_request()
    encoded_request = compress_and_encode_request(authn_request)
    return Response(content=encoded_request, media_type="text/plain")


@app.get("/sla/logout")
async def handle_logout(request: Request, response: Response):
    # Get session_id from cookies
    session_id = request.cookies.get("session_id")

    if session_id:
        await redis_mgr.delete(f"session:{session_id}")

    # Clear session_id cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        max_age=10800,
        samesite="none"   # ✅ must be lowercase string
    )

    return {"success": True, "redirect_url": "https://elearn.bits-pilani.ac.in/user/"}


@app.post("/sla/Shibboleth.sso/SAML2/POST")
async def receive_saml_response(request: Request):
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")

    if not saml_response:
        return HTMLResponse(content="<h1>SAMLResponse parameter missing</h1>", status_code=400)

    try:
        # Decode and parse SAMLResponse
        decoded_response = base64.b64decode(saml_response).decode("utf-8")
        root = ET.fromstring(decoded_response)
        namespace = {
            "saml2": "urn:oasis:names:tc:SAML:2.0:assertion",
            "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol"
        }

        # Extract attributes
        name_id = root.findtext(".//saml2:NameID", namespaces=namespace)
        if not name_id:
            return HTMLResponse(content="<h1>NameID not found in SAMLResponse</h1>", status_code=400)

        user_name = root.findtext(".//saml2:Attribute[@FriendlyName='cn']/saml2:AttributeValue", namespaces=namespace) or "Unknown User"
        user_role = root.findtext(".//saml2:Attribute[@FriendlyName='employeeType']/saml2:AttributeValue", namespaces=namespace) or "unknown"

        # Fetch courses from API
        api_url = f"https://elearn.bits-pilani.ac.in/api-proxy/v2/get-user-courses/{name_id}/"
        headers = {"Auth": AUTH_TOKEN}
        async with httpx.AsyncClient() as client:
            api_resp = await client.get(api_url, headers=headers)
            if api_resp.status_code != 200:
                return HTMLResponse(
                    content=f"<h1>Failed to fetch data from API. Status code: {api_resp.status_code}</h1>",
                    status_code=api_resp.status_code,
                )
            api_data = api_resp.json()

        # Generate session ID
        session_id = str(uuid.uuid4())
        # Store full user data in Redis (JSON)
        user_data = {
            "email": name_id,
            "name": user_name,
            "role": user_role,
            "api_data": api_data
        }
        # Use redis_mgr to store JSON string with TTL (e.g., 10800 seconds)
        await redis_mgr.setex(f"session:{session_id}", 10800, json.dumps(user_data))
        logging.info("[DEBUG] Setting cookie session_id=%s in response", session_id)

        # Build redirect response with cookie
        response = HTMLResponse(content=f"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="0; url={Redirect_Link}">
                </head>
                <body>
                    <p>Redirecting...</p>
                </body>
            </html>
        """)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            max_age=10800,
            samesite="none"   # ✅ must be lowercase string
        )

        return response

    except Exception as e:
        logging.exception("Error processing SAMLResponse")
        return HTMLResponse(content=f"<h1>Error processing SAMLResponse: {str(e)}</h1>", status_code=500)


@app.get("/sla/get-saml-data")
async def get_saml_data(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return JSONResponse(content={"error": "No session cookie"}, status_code=401)

    raw = await redis_mgr.get(f"session:{session_id}")
    if not raw:
        return JSONResponse(content={"error": "Session expired or not found"}, status_code=401)

    user_data = json.loads(raw)
    return JSONResponse(content=user_data)



@app.post("/sla/verify-session")
async def verify_session(request: Request):
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            return JSONResponse(content={"isValid": False, "error": "No session cookie"}, status_code=401)

        user_data_json = await redis_mgr.get(f"session:{session_id}")
        if not user_data_json:
            return JSONResponse(content={"isValid": False, "error": "Session expired or not found"}, status_code=401)

        user_data = json.loads(user_data_json)
        return JSONResponse(content={"isValid": True, "user": user_data})

    except Exception as e:
        logging.exception("Error verifying session")
        return JSONResponse(content={"isValid": False, "error": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_server:app", host="0.0.0.0", port=8024, reload=True)

