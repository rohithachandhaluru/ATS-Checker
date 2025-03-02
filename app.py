from flask import Flask, render_template, request
import os
import PyPDF2
import docx
import re
import spacy


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_text(file_path):
    text = ""
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

def get_keywords(text):
    stop_words = set([
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
        'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 
        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 
        'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 
        'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 
        'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
        'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
        'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
    ])
    
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    # Extract keywords using Named Entity Recognition
    keywords = {ent.text.lower() for ent in doc.ents if ent.text.lower() not in stop_words}
    
    return keywords

def extract_keywords_from_job_desc(job_desc_text):
    # Extract keywords from job description
    return get_keywords(job_desc_text)

def extract_keywords_from_resume(resume_text):
    # Extract keywords from resume
    return get_keywords(resume_text)


def calculate_match_percentage(resume_text, job_desc_text):
    message = ""

    job_keywords = extract_keywords_from_job_desc(job_desc_text)
    resume_keywords = extract_keywords_from_resume(resume_text)



    matched_keywords = job_keywords.intersection(resume_keywords)
    missing_keywords = job_keywords - resume_keywords



    match_percentage = round((len(matched_keywords) / len(job_keywords)) * 100, 2) if job_keywords else 0

    if match_percentage > 90:
        message = "Your resume is perfect for the job description. You can apply for the job."
    elif 80 < match_percentage <= 90:
        message = "You can apply for the job, but you should do a little bit of research on your skills."
    elif 70 < match_percentage <= 80:
        message = "You need to go through the relevant skills and come back again."
    else:
        message = "Poor resume. You need to develop more."

    return match_percentage, matched_keywords, missing_keywords, message

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "resume" not in request.files or "job_desc" not in request.form:
            return "Please upload both files"

        resume = request.files["resume"]
        job_desc = request.form['job_desc']

        if resume.filename == "":
            return "No selected file"

        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
        resume.save(resume_path)

        resume_text = extract_text(resume_path)

        match_percentage, matched_keywords, missing_keywords, message = calculate_match_percentage(resume_text, job_desc)

        return render_template("index.html", 
                               match_percentage=match_percentage, 
                               matched_keywords=matched_keywords, 
                               missing_keywords=missing_keywords,
                               message=message)
    return render_template("index.html", match_percentage=None)

if __name__ == "__main__":
    app.run(debug=True)