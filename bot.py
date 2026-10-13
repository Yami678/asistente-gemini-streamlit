import logging
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ==============================================================================
# CONFIGURACIÓN DE CREDENCIALES
# ==============================================================================
GEMINI_API_KEY = "AQ.Ab8RN6KM6Z42YLnk5AKKnGy-Chzf2ZaOVrdpWBj3f96uuTAZyA"
TELEGRAM_TOKEN = "8887392610:AAHjFJJBmvVxv8YjaKVskOaTwF4mGLAbmxM"

# Inicializar Cliente de Google GenAI
client = genai.Client(api_key=GEMINI_API_KEY)

# Memoria de sesiones conversacionales por id de usuario
sesiones_de_chat = {}

# ==============================================================================
# SECCIÓN DE PERSONALIZACIÓN DEL BOT
# ==============================================================================
# 1. Definición del Personaje / Instrucción del Sistema
SYSTEM_INSTRUCTION = """
Eres 'Astra', un asistente académico inteligente desarrollado para la materia de Sistemas Inteligentes.
Tu objetivo es responder de manera clara, estructurada, didáctica y respetuosa.
Si te preguntan por las actividades del laboratorio o entregas, indica amablemente que
deben consultar las indicaciones de la Dra. Aiblis Susej Herrera Palafox.
Usa formato Markdown con viñetas para explicaciones complejas.
"""

# 2. Configuración de hiperparámetros de la API
CONFIG_PERSONALIZADA = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=0.2,        # Creatividad balanceada
    max_output_tokens=500  # Límite razonable de longitud de respuesta
)

# ==============================================================================
# COMANDOS DE TELEGRAM
# ==============================================================================
async def comando_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 **¡Hola! Soy Astra, tu Asistente Inteligente Local.**\n\n"
        "Estoy listo para ayudarte con tus consultas académicas e investigaciones.\n"
        "• Usa /help para ver la lista de comandos disponibles.\n"
        "• Usa /reset si deseas reiniciar el historial de nuestra conversación."
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def comando_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ayuda = (
        "📌 **Menú de Ayuda:**\n\n"
        "• `/start` - Iniciar el servicio del bot.\n"
        "• `/help` - Desplegar esta lista de comandos.\n"
        "• `/reset` - Borrar la memoria de contexto del chat actual.\n"
        "• *Envía cualquier mensaje de texto* para interactuar con Gemini."
    )
    await update.message.reply_text(ayuda, parse_mode="Markdown")

async def comando_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_usuario = update.effective_user.id
    if id_usuario in sesiones_de_chat:
        del sesiones_de_chat[id_usuario]
        await update.message.reply_text("🧹 **Historial de conversación eliminado.** Tu próxima pregunta iniciará un nuevo chat.", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ No tienes ninguna sesión conversacional activa en este momento.")

# ==============================================================================
# PROCESAMIENTO DE MENSAJES Y RESPUESTA
# ==============================================================================
async def responder_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_usuario = update.effective_user.id
    texto_recibido = update.message.text

    # Crear o recuperar sesión conversacional aplicando la personalización
    if id_usuario not in sesiones_de_chat:
        sesiones_de_chat[id_usuario] = client.chats.create(
            model="gemini-3.8-flash",  # Modelo recomendado para desarrollo local
            config=CONFIG_PERSONALIZADA
        )
    
    chat_actual = sesiones_de_chat[id_usuario]

    # Indicador de "Escribiendo..." en Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        respuesta = chat_actual.send_message(texto_recibido)
        await update.message.reply_text(respuesta.text)
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR REGISTRADO]: {error_str}")
        if "503" in error_str or "UNAVAILABLE" in error_str:
            await update.message.reply_text("⚠️ El servidor de Gemini está momentáneamente saturado. Reintenta en unos momentos.")
        else:
            await update.message.reply_text("❌ Ocurrió un fallo en el procesamiento de la consulta.")

# ==============================================================================
# INICIALIZACIÓN DEL BOT
# ==============================================================================
def iniciar_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Registro de Handlers
    app.add_handler(CommandHandler("start", comando_start))
    app.add_handler(CommandHandler("help", comando_help))
    app.add_handler(CommandHandler("reset", comando_reset))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), responder_mensaje))

    print("✅ Bot ejecutándose exitosamente en modo Local (VS Code). Escuchando peticiones...")
    app.run_polling()

if __name__ == '__main__':
    iniciar_bot()