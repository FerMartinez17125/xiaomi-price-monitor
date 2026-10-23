# Xiaomi Price Monitor — Alertas por Telegram

Monitor en GitHub Actions para **Xiaomi 15T Pro (512 GB)** y **Xiaomi 17 (512 GB)**, exclusivamente en **Xiaomi México y Liverpool México**.

## Cómo funciona

GitHub Actions (cada hora, al minuto 17 UTC) → consulta de páginas → validación de SKU y precio → historial SQLite guardado en GitHub → análisis de ofertas → notificación automática por **Telegram** → reportes diarios, semanales y resumen actual.

No usa WhatsApp, no necesitas un servidor ni dejar encendida tu computadora. GitHub Actions puede retrasar u omitir alguna ejecución programada.

## Configura tu bot Telegram (5 pasos)

1. En **@BotFather**, crea tu bot con `/newbot`. **Nunca compartas el token**; si lo filtraste, revócalo en BotFather.
2. Abre tu bot en Telegram y pulsa **Start / Iniciar**. Envíale un mensaje como «Hola».
3. Obtén tu **Chat ID**: en una pestaña privada del navegador abre `https://api.telegram.org/botTU_TOKEN/getUpdates` reemplazando `TU_TOKEN` por el token real **solo en tu navegador**, nunca en GitHub, Issues ni este chat. En la respuesta localiza `"chat":{"id":123456789,...}`. El número es tu Chat ID (el mostrado aquí es ficticio). Si `result` está vacío, envía otro mensaje al bot y actualiza. Cierra después la pestaña privada.
4. Abre [Settings → Secrets and variables → Actions](https://github.com/FerMartinez17125/xiaomi-price-monitor/settings/secrets/actions). Agrega dos secretos de repositorio con **New repository secret**:
   - `TELEGRAM_BOT_TOKEN`: token entregado por BotFather.
   - `TELEGRAM_CHAT_ID`: número del paso 3, solamente dígitos.
5. Abre [Actions → Probar Telegram](https://github.com/FerMartinez17125/xiaomi-price-monitor/actions/workflows/telegram-test.yml) y haz clic en **Run workflow**. Debes recibir el mensaje de prueba en el chat privado.

El motor horario de GitHub ya está configurado para leer esos dos secretos y enviar alertas a **ese único chat**, sin grupos ni canales.

## Productos, metas y fuentes

Configuración en `config.json` (valores iniciales editables, **no precios actuales**):
- Xiaomi 15T Pro 512 GB: meta **$14,500 MXN**
- Xiaomi 17 512 GB: meta **$17,000 MXN**

| Fuente | Producto | Estado |
|---|---|---|
| Xiaomi México | 15T Pro 512 GB | URL configurada; precio aún no verificado |
| Xiaomi México | Xiaomi 17 512 GB | URL configurada; precio aún no verificado |
| Liverpool | Xiaomi 17 512 GB | URL configurada; precio aún no verificado |
| Liverpool | 15T Pro 512 GB | Pendiente de URL individual; deshabilitada |

**IMPORTANTE:** En la primera ejecución del 23 de octubre de 2026 se obtuvieron **0 precios válidos de 3 fuentes activas**. La integración de Telegram es independiente y puede probarse ahora; los precios requieren una mejora de extracción. El monitor no inventa ofertas, no evade bloqueos y descarta productos ambiguos, usados o con memoria incorrecta.

## Alertas

Notifica automáticamente al chat privado cuando:
- El precio alcanza el objetivo configurado.
- Baja más de 5% o más de 10% respecto a la cotización anterior de esa tienda.
- Se detecta un cupón, promoción o meses sin intereses (siempre con precio verificado).

No envía mensajes cada hora sin cambios. Las alertas pendientes se conservan en la base SQLite para reintento si falla Telegram. Una primera observación bajo el objetivo puede generar la primera notificación.

## Archivos

- `src/monitor.py`: comparación, almacenamiento, detección y cola.
- `src/telegram.py`: envío mediante Bot API oficial.
- `tests/`: tests de scraping básico y de Telegram.
- `.github/workflows/monitor.yml`: ejecución horaria.
- `.github/workflows/telegram-test.yml`: prueba manual de notificación.
- `data/prices.sqlite`: historial en GitHub.
- `reports/latest.md`: estado más reciente; `reports/daily/` y `reports/weekly/`.

## Pruebas sin instalar nada

En GitHub abre [Actions → Tests](https://github.com/FerMartinez17125/xiaomi-price-monitor/actions/workflows/tests.yml). Los tests también se ejecutan cuando se hacen cambios al código.

## Referencias oficiales

- Telegram Bot API: https://core.telegram.org/bots/api
- Tutorial de bots: https://core.telegram.org/bots/tutorial
- GitHub Actions secrets: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions
- GitHub Actions schedules: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
