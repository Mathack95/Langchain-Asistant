# app.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
from langchain_agent import build_agent

# Cargar variables del .env
load_dotenv()

# Crear app FastAPI
app = FastAPI()

# Configurar claves
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Validación de Twilio (opcional pero recomendable)
TWILIO_VALIDATOR = RequestValidator(TWILIO_AUTH_TOKEN) if TWILIO_AUTH_TOKEN else None

# Crear el agente LangChain
agent = build_agent()

# ------------------------------------------------------
# Ruta principal: cuando entra una llamada a tu número
# ------------------------------------------------------
@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    """
    Esta ruta se ejecuta cuando Twilio recibe una llamada.
    Usamos <Gather> para escuchar lo que el usuario dice.
    """
    response = VoiceResponse()
    gather = Gather(
        input="speech dtmf",
        action="/twilio/gather",
        method="POST",
        timeout=5
    )
    gather.say("Hola, gracias por llamar. ¿En qué puedo ayudarte? Por ejemplo, 'Quiero una cita el martes a las 10'.")
    response.append(gather)
    response.redirect("/twilio/voice")  # si no hay entrada, repite
    return Response(content=str(response), media_type="application/xml")

# ------------------------------------------------------
# Ruta donde Twilio manda la respuesta del usuario
# ------------------------------------------------------
@app.post("/twilio/gather")
async def twilio_gather(request: Request):
    form = await request.form()
    speech_result = form.get("SpeechResult")

    response = VoiceResponse()

    if not speech_result:
        response.say("No te entendí, ¿podrías repetir por favor?")
        response.redirect("/twilio/voice")
        return Response(content=str(response), media_type="application/xml")

    # Enviar lo que el cliente dijo al agente LangChain
    prompt = (
        f"Cliente: {speech_result}\n"
        "Asume que el usuario quiere reservar o preguntar algo. "
        "Responde con acción JSON si quieres crear evento, por ejemplo: "
        "{'action':'create_event','data':{...}} o responde texto normal."
    )

    try:
        result = agent.run(prompt)
    except Exception as e:
        result = f"Error procesando la solicitud: {e}"

    # Procesar la respuesta del agente
    if "evento" in result.lower() or "created" in result.lower():
        response.say("Perfecto. He creado la cita. Te enviaré confirmación.")
    else:
        response.say(result)

    return Response(content=str(response), media_type="application/xml")
