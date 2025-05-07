"""
Registro de Suscripciones NATS

Este módulo maneja el registro de todas las suscripciones a topics NATS.
Proporciona:

1. Registro de Handlers:
   - Conecta cada topic con su handler correspondiente
   - Maneja la suscripción asíncrona
   - Proporciona feedback del registro

2. Topics Registrados:
   - message.create: Para creación de mensajes
   - message.findAll: Para listar todos los mensajes

Notas:
- Las suscripciones se registran al inicio de la aplicación
- Cada topic está conectado a un handler específico
- Los handlers procesan los mensajes de forma asíncrona
"""

from nats.aio.client import Client as NATS

from app.handlers import handle_create, handle_find_all


async def register_nats_subscriptions(nc: NATS):
    """
    Registra todas las suscripciones al broker NATS.
    """
    await nc.subscribe("message.create", cb=handle_create)
    await nc.subscribe("message.find.all", cb=handle_find_all)
    print("🎧 Subscripciones registradas: message.create, message.find.all")
