from flask import Flask, render_template, request, send_file, session, Response, jsonify
import tempfile
import os
from gemini_translation import translate_dialogue#, process_pdf
import io
import csv

from constants import PROJECT_ID, LOCATION, SECRET_KEY

parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"

app = Flask(__name__)
app.secret_key = "secret-tunnel!-secret-tunnel!"  # Replace with a strong secret key



@app.route("/", methods=["GET", "POST"])
def index():
    translated_text = None
    filename = session.get('filename')  # Get filename from session
    target_language = session.get('target_language')

    if request.method == "POST":
        file = request.files.get("file")  # Get the file from the request
        target_language = request.form.get("target_language")
        
        # Handle optional PDF context
        pdf_context = request.files.get('pdf_context')
        if pdf_context:
            pdf = pdf_context.read()
        else:
            pdf = None

        if file:
            file_content = file.read().decode("utf-8")
            session['file_content'] = file_content
        
        if 'file_content' in session and target_language:
            file_content = session['file_content']
            print(file_content)

            # Clean up leading/trailing whitespace that might mess up parsing
            csv_string = file_content.strip()

            # Create a file-like object from the string
            f = io.StringIO(csv_string)

            # Use the csv reader to process the string
            reader = csv.reader(f)

            # Skip the header row
            next(reader, None)

            # Initialize a variable to keep track of the previous speaker
            previous_speaker = None

            # Initialize an empty string to store the formatted output
            output_string = ""

            # Process the remaining rows
            for row in reader:
                speaker, dialogue = row
                # Add double newline if the speaker changes
                if speaker != previous_speaker:
                    if output_string:  # Only add newline if output_string is not empty
                        output_string += "\n\n"
                    output_string += f"**{speaker}:** {dialogue.strip()}"  # No newline after each dialogue
                    previous_speaker = speaker
                else:
                    output_string += f" {dialogue.strip()}"  # Continue dialogue on the same line

            print(output_string)

            translated_text = translate_dialogue(pdf, [output_string], target_language)

            session['translated_text'] = translated_text

    return render_template("index.html", translated_text=translated_text)


@app.route("/download", methods=["POST"])
def download():
    translated_text = session.get('translated_text') 
    filename = session.get('filename')  # Get original filename from session
    target_language = session.get('target_language')

    # default filename when all else fails
    download_filename = "translated_text.csv"  

    if translated_text:
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_file:
            temp_file.write(translated_text)
            temp_file_path = temp_file.name

        # Read the contents of the file
        with open(temp_file_path, 'r') as f:
            translated_content = f.read()

        # Remove the temporary file
        os.remove(temp_file_path)

        if filename and target_language:
            # Construct the desired filename
            filename_parts = os.path.splitext(filename)  # Split into base and extension
            download_filename = f"{filename_parts[0]}_{target_language}{filename_parts[1]}"
        
        print(download_filename)

        return Response(translated_content, 
                        mimetype="text/plain", 
                        headers={"Content-disposition": 
                                 f"attachment; filename={download_filename}"})
    
    return "No text to download", 400 

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))