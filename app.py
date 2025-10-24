from flask import Flask, render_template, request
import PyPDF2
import random
import os

app = Flask(__name__, template_folder="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- Helper Functions ----------
def get_students_from_pdf(pdf_path):
    students = []
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        students.append(line)
    return students

def get_faculty_from_pdf(pdf_path):
    faculty = []
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        faculty.append(line)
    return faculty

def split_into_sections(students, students_per_section=75):
    sections = {}
    section_no = 1
    for i in range(0, len(students), students_per_section):
        sections[section_no] = students[i:i + students_per_section]
        section_no += 1
    return sections

subjects = ["IDP", "DMT", "IAI", "CN", "CD"]
colors = {
    "IDP": "#FF9999",  # Light Red
    "DMT": "#99CCFF",  # Light Blue
    "IAI": "#99FF99",  # Light Green
    "CN": "#FFCC99",   # Light Orange
    "CD": "#CC99FF"    # Light Purple
}
times = [("8:15", "9:55"), ("10:10", "12:40"), ("1:40", "3:20")]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

def generate_timetable_html(sections, faculty_list):
    html = "<html><head><title>Timetable</title><style>"
    html += "table {border-collapse: collapse; width: 100%; margin-bottom: 40px;} "
    html += "th, td {border: 1px solid #333; text-align: center; padding: 8px;} "
    html += "</style></head><body>"

    faculty_cycle = iter(faculty_list)

    for sec_no, students in sections.items():
        html += f"<h2>Section {sec_no}</h2>"
        html += "<table><tr><th>Time</th>"
        for day in days:
            html += f"<th>{day}</th>"
        html += "</tr>"

        for start, end in times:
            html += f"<tr><td>{start}-{end}</td>"
            for _ in days:
                subject = random.choice(subjects)
                color = colors[subject]
                try:
                    faculty = next(faculty_cycle)
                except StopIteration:
                    faculty_cycle = iter(faculty_list)
                    faculty = next(faculty_cycle)
                html += f'<td style="background:{color}">{subject}<br><small>{faculty}</small></td>'
            html += "</tr>"
        html += "</table>"

    # Faculty-Subject Mapping box
    html += "<div style='margin-top:40px;'><h3>Subject - Faculty Mapping</h3>"
    html += "<table style='border-collapse: collapse; margin: auto;'>"
    html += "<tr><th style='border:1px solid #000; padding:8px;'>Subject</th><th style='border:1px solid #000; padding:8px;'>Assigned Faculty</th></tr>"
    for faculty in faculty_list:
        parts = faculty.split('-')
        if len(parts) == 2:
            name, subject = parts
            html += f"<tr><td style='border:1px solid #000; padding:8px;'>{subject.strip()}</td><td style='border:1px solid #000; padding:8px;'>{name.strip()}</td></tr>"
    html += "</table></div>"

    html += "</body></html>"
    return html


# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    login_id = request.form.get("login-id")
    password = request.form.get("password")
    if login_id and password:
        return render_template("upload.html")
    else:
        return "Login failed! Please provide credentials."

@app.route("/upload", methods=["POST"])
def upload():
    """Handles PDF upload for students and faculty"""
    if "student_file" not in request.files or "faculty_file" not in request.files:
        return "No file part"

    student_file = request.files["student_file"]
    faculty_file = request.files["faculty_file"]

    if student_file.filename == "" or faculty_file.filename == "":
        return "No selected file"

    student_path = os.path.join(UPLOAD_FOLDER, student_file.filename)
    faculty_path = os.path.join(UPLOAD_FOLDER, faculty_file.filename)

    student_file.save(student_path)
    faculty_file.save(faculty_path)

    return render_template(
        "generate.html",
        student_pdf=student_file.filename,
        faculty_pdf=faculty_file.filename
    )

@app.route("/generate", methods=["POST"])
def generate():
    student_pdf = request.form.get("student_pdf")
    faculty_pdf = request.form.get("faculty_pdf")
    num_sections = int(request.form.get("num_sections", 1))

    student_path = os.path.join(UPLOAD_FOLDER, student_pdf)
    faculty_path = os.path.join(UPLOAD_FOLDER, faculty_pdf)

    students = get_students_from_pdf(student_path)
    faculty = get_faculty_from_pdf(faculty_path)
    sections = split_into_sections(students, students_per_section=75)

    html_content = generate_timetable_html(sections, faculty)

    timetable_path = os.path.join(UPLOAD_FOLDER, "timetable.html")
    with open(timetable_path, "w") as f:
        f.write(html_content)

    return html_content


if __name__ == "__main__":
    app.run(debug=True)
