# app.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
import requests
import openai
from langchain_agent import build_agent
import json

app = FastAPI()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Crea el agente una vez
agent = build_agent()

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VALIDATOR = RequestValidator(TWILIO_AUTH_TOKEN)

# Ruta que Twilio llamará al entrar la llamada
@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    # Validar webhook (opcional pero recomendado)
    headers = dict(request.headers)
    body = await request.form()
    # (aquí podrías validar la firma con TWILIO_VALIDATOR)

    # Usaremos <Gather> para recoger la intención; alternativa: <Record> para audio completo.
    response = VoiceResponse()
    gather = Gather(input='speech dtmf', action="/twilio/gather", method="POST", timeout=5)
    gather.say("Hola, gracias por llamar. ¿En qué puedo ayudar? Por ejemplo, 'Quiero una cita el martes a las 10'".encode('utf-8'))
    response.append(gather)
    response.redirect('/twilio/voice')  # si no hay entrada, repetir
    return Response(content=str(response), media_type="application/xml")

# Twilio envía aquí lo recogido por Gather
@app.post("/twilio/gather")
async def twilio_gather(Request: Request):
    form = await Request.form()
    speech_result = form.get("SpeechResult")  # Twilio puede enviar la transcripción si usas speech
    # Si recolectas raw audio, tendrías que usar <Record> y luego procesar la URL de recording
    if not speech_result:
        # fallback
        response = VoiceResponse()
        response.say("No te entendí, repíteme por favor.")
        response.redirect('/twilio/voice')
        return Response(content=str(response), media_type="application/xml")

    # ---> Enviar la transcripción al agente LangChain
    prompt = f"Cliente: {speech_result}\nAsume que el usuario quiere reservar o preguntar. Responde con acción JSON si quieres crear evento, por ejemplo: {{'action':'create_event', 'data':{{...}}}} o bien responde texto."
    result = agent.run(prompt)

    # Intent: si LangChain devolvió instrucción para crear evento, parsea y llama a la herramienta
    # (en este ejemplo asumimos que el agente ya llamó a la herramienta. Si no, parseamos result.)
    response = VoiceResponse()
    # Simple: si en result aparece 'Evento creado' decimos al usuario que está OK
    if "Evento creado" in result or "evento creado" in result.lower() or "created" in result.lower():
        response.say("Perfecto. He creado la cita. Te envío confirmación.")
    else:
        # devolver la respuesta conversacional
        response.say(result)
    return Response(content=str(response), media_type="application/xml")
#app.py
