import csv
import io
import json
from typing import List, Optional
from django.utils import timezone
from agent_chatbot.settings import TwilioConfig, OpenAIConfig
from chat.models import Channel, Message
from catalog.models import Vehicle, KnowledgeArticle
from openai import OpenAI
from twilio.rest import Client

class TwilioWrapper:
    """
    A wrapper class for Twilio API interactions.
    """
    def __init__(self):
        self.client = Client(TwilioConfig.ACCOUNT_SID, TwilioConfig.AUTH_TOKEN)

    def send_whatsapp(self, body: str, to_number: str, from_number: str = TwilioConfig.WHATSAPP_FROM):
        message = self.client.messages.create(
            body=body,
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}"
        )
        return message

class LLMPipeline:
    """
    Conversational RAG pipeline for the Kavak sales agent, with typo correction,
    dynamic retrieval checks, and final response generation.
    """

    def __init__(
        self,
        channel: Channel,
        model_name: str = "gpt-4-turbo",
        temperature: float = 0.5,
        classification_model: str = "gpt-3.5-turbo",
        classification_model_temperature: float = 0,
        history_size: int = 10,
        timeout_minutes: int = 15,
    ):
        """
        Initialize the pipeline with channel, models, and parameters.
        """
        if not channel:
            raise ValueError("channel must be provided to LLMPipeline.")
        self.channel = channel
        self.model = model_name
        self.temperature = temperature
        self.classification_model = classification_model
        self.classification_model_temperature = classification_model_temperature
        self.history_size = history_size
        self.timeout_minutes = timeout_minutes
        self.client = OpenAI(api_key=OpenAIConfig.API_KEY)

    def get_active_history(self) -> List[Message]:
        """
        STEP 1: Fetch the last N messages if within timeout window,
        otherwise return only the most recent message.
        """
        qs = self.channel.messages.order_by('-date_created')
        if not qs.exists():
            return []
        last = qs.first()
        if (timezone.now() - last.date_created).total_seconds() > self.timeout_minutes * 60:
            return [last]
        return list(qs[: self.history_size][::-1])

    def build_transcript(
        self,
        messages: List[Message],
        exclude_msg: Optional[Message] = None
    ) -> str:
        """
        STEP 1b: Convert messages to a human-readable transcript,
        excluding the specified message (typically the latest user message).
        """
        lines = []
        for m in messages:
            if exclude_msg and m.id == exclude_msg.id:
                continue
            author = m.author.lower() if m.author else ""
            if author in ("assistant", "bot"):
                label = "Bot"
            elif m.author:
                label = str(m.author)
            else:
                label = "Usuario"
            lines.append(f"{label}: {m.text}")
        return "\n".join(lines)

    def get_last_user_message(self) -> Optional[Message]:
        """
        STEP 2a: Return the most recent message sent by a user (not the bot).
        """
        return Message.objects.filter(channel=self.channel).exclude(author__iexact="bot").order_by('-date_created').first()

    def normalize_user_text(self, text: str) -> str:
        """
        STEP 2b: Use LLM to correct typos, accents, and normalize the user input.
        """
        prompt = [
            {
                "role": "system",
                "content": (
                    "Corrige y normaliza la siguiente frase del usuario sobre autos. "
                    "Devuelve el texto corregido en español, SIN añadir información adicional ni explicación. "
                    "Ejemplo: 'nesesito un nissan versa 2022 en guadaljara' -> "
                    "'Necesito un Nissan Versa 2022 en Guadalajara'."
                )
            },
            {"role": "user", "content": text}
        ]
        resp = self.client.chat.completions.create(
            model=self.classification_model,
            messages=prompt,
            temperature=self.classification_model_temperature
        )
        return resp.choices[0].message.content.strip()

    def should_fetch_more_vehicle_info(
        self,
        transcript: str,
        last_user_message: str
    ) -> bool:
        """
        STEP 3: Ask LLM if user requested vehicle info.
        """
        prompt = [
            {
                "role": "system",
                "content": (
                    "Eres un agente de ventas de autos de Kavak. Analiza la siguiente conversación "
                    "y determina si el usuario ha solicitado información de vehículos, marcas de vehiculos, modelos, kilometrage o rango de precios. "
                    "Este paso es importante para decidir si se debe buscar información adicional.\n\n"
                    "Analiza la seccion de Conversación, si consideras que ya se le ha proporcionado información de vehiculos "
                    "Y no se necsita buscar más información, responde 'false'. "
                    "Si necesitas mas information sobre los vehiculos, responde 'true'; de lo contrario 'false'.\n\n"
                    "Si el usuario no ha solicitado nueva información de vehiculos, responde 'false'. "
                    f"Conversación:\n{transcript}\n\n"
                    f"Último mensaje del usuario:\n{last_user_message}\n"
                )
            }
        ]
        resp = self.client.chat.completions.create(
            model=self.classification_model,
            messages=prompt,
            temperature=self.classification_model_temperature
        )
        should_fetch = True if resp.choices[0].message.content.strip().lower() == "true" else False
        return should_fetch

    def retrieve_filtered_vehicles(self, user_msg: str) -> str:
        """
        STEP 4: Dump catalog to CSV and ask LLM to filter vehicles per user query.
        Returns the filtered CSV (or an empty string if no matches).
        """
        # Load full catalog into CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'stock_id','km','price','make','model','year',
            'version','bluetooth','largo','ancho','altura','car_play'
        ])
        for v in Vehicle.objects.all():
            writer.writerow([
                v.stock_id, v.km, v.price, v.make, v.model, v.year,
                v.version, 'true' if v.bluetooth else 'false',
                v.largo, v.ancho, v.altura,
                'true' if v.car_play else 'false'
            ])
        vehicles_csv = output.getvalue()

        # Spanish prompt to filter
        system = (
            "Eres un agente de ventas de autos de Kavak. Se te proporciona un CSV con datos de vehículos. "
            "Filtra los vehículos según la siguiente consulta del usuario y devuelve un CSV "
            "con los que cumplan. No inventes nada. Si no hay coincidencias, devuelve un CSV con solo el encabezado.\n\n"
            f"Consulta:\n{user_msg}\n\n"
            f"CSV de vehículos:\n{vehicles_csv}\n\n"
            "Formato de salida:\n"
            "stock_id,km,price,make,model,year,version,bluetooth,largo,ancho,altura,car_play\n"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":system}],
            temperature=0
        )
        return resp.choices[0].message.content.strip()

    def get_relevant_kb_article_ids(self, transcript: str, last_user_message: str) -> List[str]:
        """
        STEP 4a: Ask LLM if user requested company policy or FAQs.

        """
        # 1) Fetch active articles
        kbs = list(KnowledgeArticle.objects.filter(active=True).order_by('date_created'))

        # 2) Build a list like "id: title"
        id_list = [f"{kb.id}: {kb.name}" for kb in kbs]
        id_block = "\n".join(id_list)

        # 3) Construct the Spanish prompt
        system_content = (
            "Eres un agente de ventas de autos de Kavak. "
            "A continuación tienes una lista de artículos de conocimiento en formato `id: título`:\n\n"
            f"{id_block}\n\n"
            "Basándote en la conversación previa y en la última pregunta del usuario, "
            "devuélveme un JSON con un arreglo de los IDs (UUID) de los artículos que sean relevantes. "
            "Si ninguno aplica, devuelve `[]`.\n\n"
            f"Conversación previa:\n{transcript}\n\n"
            f"Último mensaje del usuario:\n{last_user_message}\n"
            "Ejemplo de salida: [\"uuid1\", \"uuid2\"]\n\n"
        )
        prompt = [{"role": "system", "content": system_content}]
        print(f"Prompt for KB IDs:\n{system_content}")
        # 4) Call the LLM
        resp = self.client.chat.completions.create(
            model=self.classification_model,
            messages=prompt,
            temperature=0
        )
        content = resp.choices[0].message.content.strip()
        print(f"LLM response for KB IDs:\n{content}")

        # 5) Parse out the JSON array of IDs
        try:
            ids = json.loads(content)
            # ensure we only return IDs that exist in our list
            valid_ids = {str(kb.id) for kb in kbs}
            return [i for i in ids if isinstance(i, str) and i in valid_ids]
        except Exception:
            # fallback: no valid JSON, return empty list
            return []

    def load_additional_data(self, kb_ids: list) -> str:
        """
        STEP 4b: Load KBs for relevant policy/FAQ snippets.
        """
        # fetch only active articles in the given order
        articles = list(KnowledgeArticle.objects.filter(id__in=kb_ids, active=True))

        # format each as "Title\nDescription"
        snippets = [f"{a.name}\n{a.text}" for a in articles]

        # join with a blank line
        return "\n".join(snippets)

    def build_prompt(
        self,
        transcript: str,
        last_user_message: str,
        vehicle_section: str,
        extra_section: str
    ) -> List[dict]:
        """
        STEP 5: Build the final LLM prompt in Spanish, including transcript,
        last user message, filtered vehicles, and extra context.
        """
        system = (
            "Eres un agente de ventas de autos de Kavak. Responde solo usando la información proporcionada. "
            "La seccion de Conversación previa contiene la conversación previa entre el usuario y el bot. "
            "La seccion de ultimo mensaje del usuario contiene el último mensaje del usuario. Debes responder a este mensaje."
            "No inventes autos, características ni promociones. Usa solo Conversación previa y la sección de vehículos filtrados.\n\n"
            "Tambien debes de tomar en cuenta crear planes de financiamiento "
            "para los autos que el usuario solicite tomando base el enganche, el precio del auto."
            "La tasa de interes es del 10% y el plazo es de 3 a 6 años. No puedes considerar un plazo mas largo ni una tasa de interes menor.\n\n"
            "Cuando te pregunten por un financiamiento, no menciones que lo que calculaste puede cambiar. "
            "Si el CSV de vehículos no contiene informacion del vehiculo que el usuario busca, responde con un mensaje amable al usuario diciendole "
            "que el auto que busca no está disponible. Preguntale que que si tiene otro vehiculo en mente para que lo puedas buscar.\n\n"
            "Si la pregunta del usuario no tiene que ver con autos, analiza la seccion de Conversación previa y la seccion de Información adicional. "
            "Detecta si la informacion en la seccion de Información adicional es relevante para la pregunta del usuario. "
            "Para formatear tu respuesta en WhatsApp, utiliza el siguiente markdown:\n"
            "*texto* para negritas\n"
            "_texto_ para itálicas\n"
            "~texto~ para tachado\n"
            "El formato de salida es un mensaje de WhatsApp en español, "
            "sin etiquetas HTML ni encabezados, y sin emojis ni abreviaciones. No agregues markdown que no este especificado.\n\n"
            f"Último mensaje del usuario:\n{last_user_message}\n\n"
            f"Conversación previa:\n{transcript}\n\n"
            f"Vehículos filtrados (CSV):\n{vehicle_section}\n\n"
            f"Información adicional:\n{extra_section}\n"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": last_user_message}
        ]
    def call_llm(self, prompt: List[dict]) -> str:
        """
        STEP 6: Call OpenAI ChatCompletion and return text.
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            temperature=self.temperature
        )
        return resp.choices[0].message.content.strip()

    def process_response(self, reply: str) -> Message:
        """
        STEP 7: Persist the assistant's reply.
        """
        return Message.objects.create(
            channel=self.channel,
            text=reply,
            author='bot'
        )

    def process(self) -> Message:
        """
        Orchestrate the full pipeline:
          1. Fetch recent history (with timeout)
          1b. Build a transcript excluding the last user message
          2. Fetch last user message from DB
          2b. Normalize user text
          3. Decide if we should fetch vehicle info
          4. Fetch filtered vehicles (if needed)
          4a. Decide if we should fetch extra data
          4b. Fetch extra data (if needed)
          5. Build final prompt
          6. Call LLM
          7. Save and return the reply
        """
        # 1 & 1b
        history = self.get_active_history()
        last_user = self.get_last_user_message()
        user_text = last_user.text
        transcript = self.build_transcript(history, exclude_msg=last_user)
        # print(f"Last user message: {user_text}")
        # print(f"Transcript:\n{transcript}")


        # 2 & 2b
        normalized = self.normalize_user_text(user_text)
        print(f"Original user text: {user_text}")
        print(f"Normalized user text: {normalized}")

        # 3 & 4
        vehicles_csv = ""
        should_fetch_vehicle_info = self.should_fetch_more_vehicle_info(transcript, normalized)
        print(f"Should fetch vehicle info: {should_fetch_vehicle_info}")
        if should_fetch_vehicle_info:
            vehicles_csv = self.retrieve_filtered_vehicles(normalized)
            print(f"Filtered vehicles CSV:\n{vehicles_csv}")

        # 4a & 4b
        extra = ""
        kb_ids = self.get_relevant_kb_article_ids(transcript, normalized)
        print(f"Fetch KBs: {kb_ids}")
        if kb_ids and isinstance(kb_ids, list) and len(kb_ids) > 0:
            extra = self.load_additional_data(kb_ids)
            print(f"Extra data:\n{extra}")

        # 5
        prompt = self.build_prompt(transcript, normalized, vehicles_csv, extra)
        print(f"Final prompt:\n{prompt}")

        # 6
        reply = self.call_llm(prompt)
        print(f"LLM reply:\n{reply}")
        
        # 7
        return self.process_response(reply)
