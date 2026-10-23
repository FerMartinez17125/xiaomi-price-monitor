# Monitor de precios Xiaomi — México

Monitor gratuito de ejecución (GitHub Actions + Python) para **Xiaomi 15T Pro 512 GB y Xiaomi 17 512 GB**. Tiendas: **Xiaomi Oficial México y Liverpool México**, exclusivamente.

## Arquitectura

GitHub Actions cada hora → validación de precios → SQLite guardado en el repositorio → alertas por **WhatsApp Business Platform (API oficial Meta)** → reportes `reports/latest.md`, diarios y semanales.

**Limitación real de scraping:** las tiendas pueden no mostrar precio y memoria en HTML/JSON-LD, impedir bots o cambiar su web. El monitor no evade bloqueos ni inventa precios. Hasta la primera ejecución: **0 precios verificados en 3 fuentes activas**. Se necesita mejorar las fuentes por separado para lograr alertas reales.

## Configurar WhatsApp (en lugar de Telegram)

**Importante:** GitHub no puede enviar WhatsApp desde tu cuenta personal. Meta exige un emisor de WhatsApp Business Platform. Meta puede cobrar por las plantillas entregadas. No hay conexión a WhatsApp hasta completar estas credenciales.

1. Accede a https://developers.facebook.com/ y crea una app de Meta con el caso de uso de **WhatsApp Business**. Activa **WhatsApp Cloud API / API Setup**. La interfaz y requisitos de Meta pueden cambiar.
2. En **API Setup**, Meta ofrece un número emisor de prueba y un **Access Token temporal**. En destinatarios autorizados, agrega tu número personal, verifica el código y selecciona ese destinatario. **El número receptor es diferente del número emisor**.
3. En tu repositorio ve a **Settings → Secrets and variables → Actions → New repository secret** y crea:
   - `WHATSAPP_ACCESS_TOKEN`: token de acceso de Meta. **Temporal para probar; en producción crea un token de usuario de sistema con permisos adecuados.**
   - `WHATSAPP_PHONE_NUMBER_ID`: **Phone Number ID**, distinto del número telefónico que muestra Meta.
   - `WHATSAPP_TO`: destinatario de WhatsApp, solo dígitos con código de país. En México suele ser `521` seguido de los 10 dígitos, o el `wa_id` que indique Meta para tu cuenta. **No introduzcas tu número en `config.json` ni en el README.**
4. Abre **Actions → Probar WhatsApp oficial (Meta) → Run workflow**. Enviará la plantilla de prueba `hello_world` de Meta al destinatario autorizado. Es solo una prueba; Meta puede aceptar un envío sin confirmar su entrega, y necesitarás revisar tu WhatsApp.
5. **Para alertas automáticas de producción fuera de la ventana de 24 horas**, abre WhatsApp Manager de Meta → Message Templates. Crea y solicita aprobación de la siguiente plantilla (nombre exacto `xiaomi_monitor_aviso`, idioma `Spanish (Mexico) / es_MX`, categoría **Marketing** — las alertas de precio son ofertas, no utilidades de transacción). El nombre es una PROPUESTA que debes registrar y aprobar, **no existe automáticamente**.

### Texto exacto de la plantilla propuesta

```text
Monitor Xiaomi: aviso de oferta.
Producto: {{1}}
Tienda: {{2}}
Precio: {{3}}
Motivo: {{4}}
Enlace: {{5}}

Confirma existencia, precio y condiciones con la tienda antes de comprar.
```

Meta puede requerir ejemplos realistas para cada variable o rechazar/modificar el texto. El orden de los 5 parámetros ya está configurado en `src/whatsapp.py`. Las alertas funcionan únicamente después de que Meta apruebe esta plantilla (o cambies el código para usar otra aprobada).

6. Para uso continuado, configura en Meta un **número emisor real** y un token de acceso apropiado; consulta los requisitos de Meta y habilita facturación si aplica. El emisor de prueba está limitado a destinatarios de prueba y no es una configuración de producción 24/7.

### Cómo probar

El workflow **Probar WhatsApp oficial (Meta)** envía `hello_world` (ya preaprobada en entornos de prueba, cuando esté habilitada). El monitor principal solo envía la plantilla de 5 variables `xiaomi_monitor_aviso` si detecta un cambio de precio o cruza el objetivo. **No envía mensajes diarios por falta de precio**, para reducir costos.

### Credenciales y privacidad

Nunca pegues tokens ni el teléfono en este repositorio público, en Issues o logs. Guárdalos en GitHub Actions Secrets. **No compartas el token en el chat.**

### Costos

GitHub Actions puede ser gratuito dentro de los límites disponibles para tu repositorio público. WhatsApp Cloud API puede cobrar por mensajes de plantilla **entregados**, y las notificaciones de ofertas suelen clasificarse como **Marketing**. Revisa precios actuales en https://developers.facebook.com/docs/whatsapp/pricing antes de habilitar envíos. Es una plataforma más compleja que Telegram; no prometemos uso gratuito permanente.

## Objetivos iniciales

En `config.json` (modificables):
- Xiaomi 15T Pro 512 GB: $14,500 MXN
- Xiaomi 17 512 GB: $17,000 MXN

Se envían alertas cuando se cruza el objetivo, un precio baja más de 5% o 10%, o aparece un cupón, promoción o MSI (solo si se verifica un precio válido). El sistema compara cotizaciones válidas entre Xiaomi y Liverpool.

## Pruebas

Las pruebas locales y de integración simulada se ejecutan en **Actions → Tests** cada vez que cambia el código. También puedes ejecutar:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.monitor
```

## Fuentes

- Documentación oficial Meta WhatsApp: https://www.postman.com/meta/whatsapp-business-platform/folder/o48mro7/messages
- Documentación GitHub Actions: https://docs.github.com/en/actions
- Gestión de secretos GitHub: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions
- Plantillas y reglas 24 horas: https://www.twilio.com/docs/whatsapp/key-concepts
