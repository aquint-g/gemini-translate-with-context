import base64
import vertexai
import csv
import json
from vertexai.generative_models import GenerativeModel, SafetySetting, Part, GenerationConfig
from constants import GEMINI_MODEL, LOCATION, PROJECT_ID


def translate_dialogue(
    pdf,
    dialogue_script,
    target_language,
    project=PROJECT_ID,  
    location=LOCATION,  
    model_name= GEMINI_MODEL,  
):
    """
    Translates a dialogue script based on context from a PDF file.

    Args:
        pdf_file_path: Path to the PDF file containing context for the dialogue.
        dialogue_script: The dialogue script to be translated.
        target_language: The language to translate the dialogue into.
        project: Your Google Cloud project ID.
        location: The location of your Vertex AI resources.
        model_name: The name of the Gemini model to use.

    Returns:
        The translated dialogue script.
    """

    vertexai.init(project=project, location=location)
    model = GenerativeModel(model_name)
    chat = model.start_chat()
    
    response_schema = {
        "type": "array",  # The overall response is an array of dialogue lines
        "items": {
            "type": "object",  # Each dialogue line is an object
            "properties": {
            "Speaker": {"type": "string"},  # Speaker property (string)
            "Dialogue": {"type": "string"}  # Dialogue property (string)
            },
            "required": ["Speaker", "Dialogue"]  # Both properties are required
        }
    }

    generation_config = GenerationConfig(
        max_output_tokens= 8192,
        temperature= 1,
        top_p= 0.95,
        response_mime_type="application/json",
        response_schema=response_schema
    )

    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.OFF
        ),
    ]

    prompt = f"""You are a translation expert who's job is to localize scripts from French to {target_language}, who takes special care in keeping the spirit of the characters consistant from their source langauge to their target language.
    You have the larger body of work at your disposal to use as a sytle guide for the characters you are in charge of translating.

    {dialogue_script}

    * Translate the conversation into {target_language} with careful consideration of the style for each of the characters verbiage and speech patterns and be mindful of any portmanteaus that exist.
    
    """

    text = Part.from_text(prompt)
    # to add different sources of context: like txt, word, etc
    if pdf:
        # -- with grounding using all Harry Pooter and the rock from Phili --
        document = Part.from_data(
            mime_type="application/pdf",
            data=base64.b64decode(base64.b64encode(pdf))
        )

        response = chat.send_message(
            [document,text],
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    else:
        # -- No Phili rock, very sad :( --
        response = chat.send_message(
            [text],
            generation_config=generation_config,
            safety_settings=safety_settings
        )

    output = json.loads(response.text)
    #print(output)
    #output = "<table><tr><th>Speaker</th><th>Dialogue</th></tr>\n" + "\n".join([f"""<tr><td>{item['Speaker']}</td> <td>"{item['Dialogue']}"</td></th> """ for item in output]) +"</table>"
    #print(output)

    return output