# Xiaomi Price Monitor — Alertas por Telegram

Monitor en GitHub Actions para **Xiaomi 15T Pro (512 GB)** y **Xiaomi 17 (512 GB)**, exclusivamente en **Xiaomi México y Liverpool México**.

## Cómo funciona

GitHub Actions (cada hora, al minuto 17 UTC) → consulta de páginas → validación de SKU y precio → historial SQLite guardado en GitHub → análisis de ofertas → notificación automática por **Telegram** → reportes diarios, semanales y resumen actual.

No usa WhatsApp, no necesitas un servidor ni dejar encendida tu computadora. GitHub Actions puede retrasar u omitir alguna ejecución programada.

## Vincular tu bot sin copiar manualmente el Chat ID

1. Abre [@FerXiaomiPriceBot](https://t.me/FerXiaomiPriceBot) y pulsa **Start / Iniciar**.
2. Confirma en **Settings → Secrets and variables → Actions** que exista el secreto `TELEGRAM_BOT_TOKEN`. Por seguridad, usa un token **nuevo** si el anterior se publicó o compartió. No pegues el token en este repositorio.
3. Elige un código de vinculación privado y difícil de adivinar, de **12 a 64 caracteres alfanuméricos**, guion o guion bajo. Por ejemplo, usa tu propio valor aleatorio, no un ejemplo público.
4. En el chat privado con el bot envía `/vincular TU_CODIGO` (reemplaza `TU_CODIGO` por el valor elegido).
5. Durante los siguientes **10 minutos**, abre [Actions → Vincular Telegram](https://github.com/FerMartinez17125/xiaomi-price-monitor/actions/workflows/telegram-pair.yml), pulsa **Run workflow**, introduce exactamente el mismo código en el campo **codigo** y confirma.
6. La acción identifica exclusivamente el chat privado que haya enviado ese código, cifra el Chat ID con una clave derivada del token del bot y lo guarda como `data/telegram_chat.enc`. **El Chat ID no queda publicado en texto claro, ni necesitas crear `TELEGRAM_CHAT_ID`.**
7. Si la vinculación y su commit finalizan correctamente, recibirás en Telegram una confirmación. También puedes usar [Actions → Probar Telegram](https://github.com/FerMartinez17125/xiaomi-price-monitor/actions/workflows/telegram-test.yml) para enviar otro mensaje.

**Seguridad:** no incluyas información personal en el código de vinculación. Los inputs de Actions pueden ser visibles para colaboradores o registros según la configuración; por ello el código es temporal, debe ser aleatorio y la comprobación limita a mensajes privados recientes. El token es el único secreto persistente necesario. Si cambias el token, **debes repetir la vinculación**, porque el Chat ID cifrado anterior ya no se podrá descifrar. Si tienes un Chat ID guardado en secreto, el monitor también lo admite como alternativa.

## Productos, metas y fuentes

Configuración en `config.json` (valores iniciales editables, **no precios actuales**):
- Xiaomi 15T Pro 512 GB: meta **$14,500 MXN**
- Xiaomi 17 512 GB: meta **$17,000 MXN**

| Fuente | Producto | Estado |
|---|---|---|
| Xiaomi México | 15T Pro 512 GB | Consulta automática pausada: requiere autorización |
| Xiaomi México | Xiaomi 17 512 GB | Consulta automática pausada: requiere autorización |
| Liverpool | Xiaomi 17 512 GB | Extractor ajustado para importes repetidos; requiere nueva ejecución real |
| Liverpool | 15T Pro 512 GB | Pendiente de URL individual; deshabilitada |

**ESTADO:** La primera ejecución del 23 de octubre de 2026 obtuvo **0 precios válidos de 3 fuentes activas**. Se añadió un extractor alternativo conservador para **Liverpool Xiaomi 17 512 GB**, que identifica el código de artículo, la memoria, el precio del producto (sin confundir mensualidades ni seguros) y la opción de compra. Sus pruebas automatizadas pasaron; **todavía falta comprobarlo en la próxima ejecución real de Monitor precios Xiaomi**. Las fichas de Xiaomi México siguen mostrando $0 en HTML sin JavaScript, por lo que están pendientes. No se inventan precios ni se eluden restricciones.


**Restricción legal:** Los [términos oficiales de Xiaomi México](https://www.mi.com/mx/support/terms/terms-of-use/) restringen el uso de herramientas automáticas de extracción de datos y la creación de bases propias con su contenido sin autorización expresa. Por ello, las fuentes `mi-15t-pro` y `mi-17` están deshabilitadas en `config.json`, aunque sus enlaces se conservan para referencia. Si Xiaomi concede una fuente autorizada, podrán habilitarse de nuevo. El `robots.txt` de Liverpool permite acceso general, pero esto no garantiza disponibilidad ni derechos ilimitados sobre el contenido.

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
