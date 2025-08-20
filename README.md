# Odoo 18 GPT Integration

## Descripción
Este proyecto implementa un conjunto de módulos para **Odoo 18 Community Edition** que integran **ChatGPT** en distintos flujos de negocio:
- Atención automática en **website_livechat** con fallback a humano.
- Enriquecimiento de **leads** en CRM con datos estructurados.
- Opcionalmente, uso de **RAG** (Retrieval Augmented Generation) con documentos internos.
- Preparación de datasets para **fine-tuning** en OpenAI.

La arquitectura es **modular**, manteniendo separación clara de responsabilidades y reutilizando lo útil de módulos existentes (`is_chatgpt_integration`, `much_automated_agent_actions`, `odoo_gpt_chat`).

---

## Estructura planeada de módulos

- **gpt_core**
  - Configuración de API key, modelo, temperatura, límites.
  - `max_tokens` ahora alimenta `max_output_tokens` de la Responses API.
  - Servicios: `gpt.service.complete()` y `gpt.service.retrieve_and_complete()`.
  - Logs de tokens y coste por conversación.

- **livechat_gpt**
  - Hook a `website_livechat` para que ChatGPT responda por defecto.
  - Soporte de triggers para transferencia a humano (`/asesor`, keywords, baja confianza, falta de datos).
  - Mensajes de transición al cliente.

- **crm_lead_enrichment**
  - Campos adicionales: `x_gpt_summary`, `x_priority`, `x_missing_fields`, `x_next_step`, `x_confidence`.
  - Enriquecimiento automático al crear/actualizar leads.
  - Botón manual “Enriquecer con IA”.

- **kb_rag** *(opcional)*
  - Indexación de documentos (PDF, DOCX) en `pgvector` o `Qdrant`.
  - Función `retrieve(query, k)` integrada en `gpt.service`.

- **fine_tuning**
  - Exportación de logs en formato JSONL (`train.jsonl`, `valid.jsonl`).
  - Scripts para `openai api fine_tunes.create`.
  - Configuración de modelo fine-tuned en `ir.config_parameter`.

---

## Observaciones del análisis inicial

### Sobre `is_chatgpt_integration`
- Instalación posible en Odoo 18 CE, pero con limitaciones:
  - Override global de `_notify_thread` → puede generar efectos colaterales.
  - Crea un usuario inseguro (`chatgpt/chatgpt`) → vector de ataque.
  - Configuración con `config_parameter` mal escrito (`chatgp_model`).
  - Controller `/chatgpt_form` apunta a una plantilla inexistente.
  - Sólo funciona en canal #ChatGPT de `Discuss`, no en `website_livechat`.

### Reutilizable
- Modelo `chatgpt.model` + datos de modelos (`gpt-4o`, `gpt-4o-mini`, etc.).
- Fragmento de integración con SDK OpenAI.
- Vista de ajustes con API key (corrigiendo typo y labels).

### Recomendación
- No usar como dependencia directa.
- Crear un **fork** (`is_chatgpt_integration_fork`) con:
  - Fix del `config_parameter`.
  - Eliminación del usuario inseguro o password aleatorio + desactivación.
  - Corrección/limpieza del controller.
  - Restricción del override a canal específico.
- Encima de ese fork construir `gpt_core`.

---

## Consideraciones de seguridad
- Anonimizar PII (no RFC, CURP, direcciones exactas).
- Respuestas limitadas a <900 caracteres.
- Prevenir loops bot→bot.
- Mantener arquitectura limpia y mantenible.

---

## Roadmap
1. Crear **fork** mínimo de `is_chatgpt_integration`.
2. Implementar módulo **gpt_core** con servicio central de integración.
3. Añadir **livechat_gpt** y probar en sitio real.
4. Desarrollar **crm_lead_enrichment** y validar flujos.
5. Extender con **kb_rag** y **fine_tuning**.

---

## Licencia
AGPL-3. El código base reutilizado de `is_chatgpt_integration` hereda la misma licencia.
