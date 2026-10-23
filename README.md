# Xiaomi Price Monitor — México

Monitor de Xiaomi 15T Pro y Xiaomi 17 (ambos 512 GB), exclusivamente en **Xiaomi Oficial México** y **Liverpool México**.

## Funcionamiento
GitHub Actions → Python: consulta autorizada de páginas y verificación de modelo, memoria y precio → SQLite en `data/prices.sqlite` → comparación, alertas por Telegram y reportes en `reports/` → commit al repositorio.

Se ejecuta automáticamente cada hora (minuto 17 UTC). Los eventos programados en GitHub son best effort y pueden retrasarse u omitirse. No es necesario mantener tu PC encendida.

## Cobertura actual
| Producto | Tienda | Estado |
|---|---|---|
| 15T Pro 512 GB | Xiaomi Oficial | URL configurada, extracción real pendiente de verificar |
| Xiaomi 17 512 GB | Xiaomi Oficial | URL configurada, extracción real pendiente de verificar |
| Xiaomi 17 512 GB | Liverpool | URL configurada, extracción real pendiente de verificar |
| 15T Pro 512 GB | Liverpool | Sin URL específica confirmada, fuente deshabilitada |

El monitor **solo acepta precios reales cuando el HTML contiene un producto 512 GB con datos estructurados de oferta inequívocos**. Las páginas con precio generado solo por JavaScript pueden producir errores; no se simulan precios ni se evaden restricciones.

## Primer uso
1. Abre **Actions → Monitor precios Xiaomi → Run workflow**.
2. Revisa los logs de las fuentes.
3. Verifica el archivo `reports/latest.md` y la base `data/prices.sqlite`, creados o actualizados por Actions.

## Telegram
1. Crea un bot con [@BotFather](https://t.me/BotFather): envía `/newbot`.
2. Envía `/start` a tu bot.
3. Abre privadamente `https://api.telegram.org/botTU_TOKEN/getUpdates` y ubica `message.chat.id`. No compartas el token.
4. En este repositorio abre **Settings → Secrets and variables → Actions** y agrega `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
5. Ejecuta de nuevo el workflow. Los mensajes pendientes se conservan para reintento cuando se configure Telegram.

## Personalización
Los objetivos actuales en `config.json` son configurables: **$14,500 MXN para 15T Pro** y **$17,000 MXN para Xiaomi 17**. Son valores de inicio, no cotizaciones ni precios recomendados.

Alertas: precio bajo objetivo, caídas >5% y >10%, nuevas promociones, cupones y meses sin intereses anunciados. Las condiciones de promociones pueden necesitar confirmación en la tienda.

## Pruebas
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.monitor
```

Los resultados e historial quedan persistidos en GitHub, aunque el runner de Actions use almacenamiento temporal durante la ejecución.

## Referencias técnicas
- [GitHub Actions: eventos programados](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [GitHub Actions: secretos](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage)
- [Xiaomi México](https://www.mi.com/mx/)
