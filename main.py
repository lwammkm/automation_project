from fastapi.responses import StreamingResponse
import io
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import mysql.connector
import os
import subprocess

app = FastAPI()

def connect_to_database():
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'DEJ'),
        password=os.environ.get('MYSQL_PASSWORD', '1234'),
        database=os.environ.get('MYSQL_DATABASE', 'candidates_resumes'),
    )

def get_person_cv_by_id(candidate_id, cursor):
    cursor.execute("SELECT * FROM candidates WHERE candidate_id = %s", (candidate_id,))
    candidate_row = cursor.fetchall()
    if not candidate_row:
        return None, None, None, None

    cursor.execute("SELECT * FROM education WHERE candidate_id = %s", (candidate_id,))
    education_row = cursor.fetchall()

    cursor.execute("SELECT * FROM experience WHERE candidate_id = %s", (candidate_id,))
    experience_row = cursor.fetchall()

    cursor.execute("SELECT * FROM projects WHERE candidate_id = %s", (candidate_id,))
    projects_row = cursor.fetchall()

    return candidate_row, education_row, experience_row, projects_row


def get_person_cv_by_name(full_name, cursor):
    cursor.execute("SELECT candidate_id FROM candidates WHERE full_name = %s", (full_name,))
    contact_row = cursor.fetchall()
    if not contact_row:
        return None, None, None, None
    candidate_id = contact_row[0][0]
    # Add this line for debugging
    print(f"Retrieved candidate ID for '{full_name}': {candidate_id}")

    # Unpack values correctly from get_person_cv_by_id
    candidate_row, education_row, experience_row, projects_row = get_person_cv_by_id(candidate_id, cursor)

    return candidate_row, education_row, experience_row, projects_row


def generate_cv_content(cursor, candidate_id, full_name, professional_title, location, institute, degree_name,
start_date, end_date, experience_content, projects_content, logo_file_path):
    languages_query = """
        SELECT languages.language_name
        FROM candidates_language
        LEFT JOIN languages ON candidates_language.language_id = languages.language_id
        WHERE candidates_language.candidate_id = %s
        """
    cursor.execute(languages_query, (candidate_id,))
    languages_row = cursor.fetchall()

    languages = [lang[0] for lang in languages_row]

    # Join the language names with commas
    languages = ", ".join(languages) if languages else ""

    frameworks_query = """
       SELECT frameworks.framework
       FROM candidates_framework
       LEFT JOIN frameworks ON candidates_framework.framework_id = frameworks.framework_id
       WHERE candidates_framework.candidate_id = %s
       """
    cursor.execute(frameworks_query, (candidate_id,))
    frameworks_row = cursor.fetchall()
    framework = ", ".join([fw[0] for fw in frameworks_row]) if frameworks_row else ""

    # Fetch database_names
    database_names_query = """
       SELECT database_names.database_name
       FROM candidates_database
       LEFT JOIN database_names ON candidates_database.database_id = database_names.database_id
       WHERE candidates_database.candidate_id = %s
       """
    cursor.execute(database_names_query, (candidate_id,))
    database_names_row = cursor.fetchall()
    database_name = ", ".join([db[0] for db in database_names_row]) if database_names_row else ""
    devops_query = """
        SELECT devops.devop_name
        FROM candidates_devop
        LEFT JOIN devops ON candidates_devop.devop_id = devops.devop_id
        WHERE candidates_devop.candidate_id = %s
        """
    cursor.execute(devops_query, (candidate_id,))
    devops_row = cursor.fetchall()
    devops = ", ".join([dev[0] for dev in devops_row]) if devops_row else ""

    # Query the new additional technologies join tables individually
    # Query for additionalTech_languages
    cursor.execute("""
        SELECT languages.language_name
        FROM additionaltech_languages AS atl
        LEFT JOIN languages ON atl.language_id = languages.language_id
        WHERE atl.candidate_id = %s
    """, (candidate_id,))
    language_row = cursor.fetchall()
    language_list = [lang[0] for lang in language_row]

    # Query for additionalTech_frameworks
    cursor.execute("""
        SELECT frameworks.framework
        FROM additionaltech_frameworks AS atf
        LEFT JOIN frameworks ON atf.framework_id = frameworks.framework_id
        WHERE atf.candidate_id = %s
    """, (candidate_id,))
    framework_row = cursor.fetchall()
    framework_list = [fw[0] for fw in framework_row]

    # Query for additionalTech_databases
    cursor.execute("""
        SELECT database_names.database_name
        FROM additionaltech_databases AS atd
        LEFT JOIN database_names ON atd.database_id = database_names.database_id
        WHERE atd.candidate_id = %s
    """, (candidate_id,))
    database_row = cursor.fetchall()
    database_list = [db[0] for db in database_row]

    # Query for additionalTech_devops
    cursor.execute("""
        SELECT devops.devop_name
        FROM additionaltech_devops AS atdev
        LEFT JOIN devops ON atdev.devop_id = devops.devop_id
        WHERE atdev.candidate_id = %s
    """, (candidate_id,))
    devops_row = cursor.fetchall()
    devops_list = [dev[0] for dev in devops_row]

    # Combine all the lists into one
    all_technologies = [language_list, framework_list, database_list, devops_list]

    # Flatten the nested lists and filter out empty strings
    tech_list = ", ".join(filter(None, [tech for sublist in all_technologies for tech in sublist]))
    formatted_tech_list = f"\\resumeItem{{{tech_list}}}"



    cv_content = f"""
    \\documentclass[a4paper,12pt]{{article}}
     \\usepackage[utf8]{{inputenc}}
    \\usepackage{{graphicx}}
    \\usepackage{{verbatim}}

    \\usepackage{{titlesec}}

    \\usepackage{{color}}

    \\usepackage{{enumitem}} 

    \\usepackage{{fancyhdr}}

    \\usepackage{{tabularx}}

    \\usepackage{{latexsym}}

    \\usepackage{{marvosym}}

    \\usepackage{{fullpage}}

    \\usepackage[hidelinks]{{hyperref}}

    \\usepackage[normalem]{{ulem}}

    \\usepackage[english]{{babel}}

    \\input glyphtounicode 
    \\pdfgentounicode=1 

    \\usepackage[default]{{sourcesanspro}}
    \\urlstyle{{same}} 
    \\pagestyle{{fancy}} 
    \\fancyhf{{}}
    \\renewcommand{{\\headrulewidth}}{{0in}}
    \\renewcommand{{\\footrulewidth}}{{0in}} 
    \\setlength{{\\tabcolsep}}{{0in}}
    \\addtolength{{\\oddsidemargin}}{{-0.5in}}
    \\addtolength{{\\topmargin}}{{-0.5in}}
    \\addtolength{{\\textwidth}}{{1.0in}}
    \\addtolength{{\\textheight}}{{1.0in}}
    \\raggedbottom{{}}
    \\raggedright{{}}
    \\titleformat{{\\section}}
      {{\\large}}{{}}
        {{0em}}{{\\color{{blue}}}}[\\color{{black}}\\titlerule\\vspace{{0pt}}]
    \\renewcommand\\labelitemii{{$\\vcenter{{\\hbox{{\\tiny$\\bullet$}}}}$}}
    \\newcommand{{\\resumeItem}}[1]{{
      \\item\\small{{#1}}
    }}
    \\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[rightmargin=0.15in]}}
    \\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}}}
    \\newcommand{{\\resumeSectionType}}[3]{{
      \\item\\begin{{tabular*}}{{0.96\\textwidth}}[t]{{
        p{{0.18\\linewidth}}p{{0.02\\linewidth}}p{{0.81\\linewidth}}
      }}
        \\textbf{{#1}} & #2 & #3
      \\end{{tabular*}}\\vspace{{-2pt}}
    }}
    \\newcommand{{\\resumeTrioHeading}}[3]{{
      \\item\\small{{
        \\begin{{tabular*}}{{0.96\\textwidth}}[t]{{
          l@{{\\extracolsep{{\\fill}}}}c@{{\\extracolsep{{\\fill}}}}r
        }}
          \\textbf{{#1}} & \\textit{{#2}} & #3
        \\end{{tabular*}}
      }}
    }}
    \\newcommand{{\\resumeQuadHeading}}[4]{{
      \\item
      \\begin{{tabular*}}{{0.96\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
        \\textbf{{#1}} & #2 \\\\
        \\textit{{#3}} & #4 \\\\
      \\end{{tabular*}}
    }}
    \\newcommand{{\\resumeQuadHeadingChild}}[2]{{
      \\item
      \\begin{{tabular*}}{{0.96\\\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
        \\textbf{{\\small#1}} & {{\\small#2}} \\\\
      \\end{{tabular*}}
    }}
    \\newcommand{{\\resumeHeadingListStart}}
    {{
      \\begin{{itemize}}[leftmargin=0.15in, label={{}}]
    }}
    \\newcommand{{\\resumeHeadingListEnd}}
    {{\\end{{itemize}}
    }}
    \\begin{{document}}
    \\hfill
    \\includegraphics[height=1.5cm]{{{logo_file_path}}}
    \\section{{Contact Information}}
      \\resumeHeadingListStart{{}}
        \\resumeSectionType{{Full name}}{{}} {{{full_name}}}
        \\resumeSectionType{{Professional title}}{{}} {{{professional_title}}}
        \\resumeSectionType{{Location}}{{}} {{{location}}}
      \\resumeHeadingListEnd{{}}
    \\section{{Education}}
      \\resumeHeadingListStart{{}}
        \\resumeQuadHeading {{{institute}}}{{{start_date}}}
        {{{degree_name}}}{{{end_date}}}
      \\resumeHeadingListEnd{{}}
      """

    languages_content = ""
    framework_content = ""
    database_content = ""
    devops_content = ""

    if languages:
        languages_content = f"\\resumeSectionType{{Languages}}{{}} {{{languages}}}"

    if framework:
        framework_content = f"\\resumeSectionType{{Frameworks}}{{}} {{{framework}}}"

    if database_name:
        database_content = f"\\resumeSectionType{{Databases}}{{}} {{{database_name}}}"

    if devops:
        devops_content = f"\\resumeSectionType{{DevOps}}{{}} {{{devops}}}"

    cv_content += f"""
    \\section{{Key Skills and Qualifications}}
      \\resumeHeadingListStart{{}}
        {languages_content}
        {framework_content}
        {database_content}
        {devops_content}
      \\resumeHeadingListEnd{{}}
    """

    cv_content += f""" 
    \\section{{Professional (years of) Experience}}
    \\resumeHeadingListStart{{}}
          {experience_content}
       \\resumeHeadingListEnd{{}}
    """

    # Include the Projects section if there is content
    if projects_content:
        cv_content += f"""
    \\section{{Projects}}
      \\resumeHeadingListStart{{}}
        {projects_content}
         \\resumeHeadingListEnd{{}}
    """

    # Include the Other Technologies section if there is content
    if tech_list:
        cv_content += f"""
    \\section{{Other Technologies Used}}
    \\resumeHeadingListStart{{}}
    \\resumeItemListStart{{}}
    {{{formatted_tech_list}}}
    \\resumeItemListEnd{{}}
    \\resumeHeadingListEnd{{}}
    """

    cv_content += f"""
    \\rfoot{{\\hfill
    DEJ Technology GmbH\\\\
    Zu den Tannen 1a, 18107 Elmenhorst-Lichtenhagen\\\\
    Geschäftsführer Dr. Jonas Flint und Dipl. Wirt.-Inf. Erik Heidenreich}}
    \\end{{document}}
    """
    return cv_content


def generate_internal_cv_content(cursor, candidate_id, full_name, professional_title, location, phone_number, email,
 experience_years, technical_rating, nontechnical_rating, minimum_salary_expectation, last_cv_update, additional_notes,
 institute, degree_name, start_date, end_date, experience_content, projects_content, logo_file_path):
    languages_query = """
        SELECT languages.language_name
        FROM candidates_language
        LEFT JOIN languages ON candidates_language.language_id = languages.language_id
        WHERE candidates_language.candidate_id = %s
        """
    cursor.execute(languages_query, (candidate_id,))
    languages_row = cursor.fetchall()

    languages = [lang[0] for lang in languages_row]

    # Join the language names with commas
    languages = ", ".join(languages) if languages else ""


    frameworks_query = """
       SELECT frameworks.framework
       FROM candidates_framework
       LEFT JOIN frameworks ON candidates_framework.framework_id = frameworks.framework_id
       WHERE candidates_framework.candidate_id = %s
       """
    cursor.execute(frameworks_query, (candidate_id,))
    frameworks_row = cursor.fetchall()
    framework = ", ".join([fw[0] for fw in frameworks_row]) if frameworks_row else ""

    # Fetch database_names
    database_names_query = """
       SELECT database_names.database_name
       FROM candidates_database
       LEFT JOIN database_names ON candidates_database.database_id = database_names.database_id
       WHERE candidates_database.candidate_id = %s
       """
    cursor.execute(database_names_query, (candidate_id,))
    database_names_row = cursor.fetchall()
    database_name = ", ".join([db[0] for db in database_names_row]) if database_names_row else ""
    devops_query = """
        SELECT devops.devop_name
        FROM candidates_devop
        LEFT JOIN devops ON candidates_devop.devop_id = devops.devop_id
        WHERE candidates_devop.candidate_id = %s
        """
    cursor.execute(devops_query, (candidate_id,))
    devops_row = cursor.fetchall()
    devops = ", ".join([dev[0] for dev in devops_row]) if devops_row else ""

    # Query the new additional technologies join tables individually
    # Query for additionalTech_languages
    cursor.execute("""
        SELECT languages.language_name
        FROM additionaltech_languages AS atl
        LEFT JOIN languages ON atl.language_id = languages.language_id
        WHERE atl.candidate_id = %s
    """, (candidate_id,))
    language_row = cursor.fetchall()
    language_list = [lang[0] for lang in language_row]

    # Query for additionalTech_frameworks
    cursor.execute("""
        SELECT frameworks.framework
        FROM additionaltech_frameworks AS atf
        LEFT JOIN frameworks ON atf.framework_id = frameworks.framework_id
        WHERE atf.candidate_id = %s
    """, (candidate_id,))
    framework_row = cursor.fetchall()
    framework_list = [fw[0] for fw in framework_row]

    # Query for additionalTech_databases
    cursor.execute("""
        SELECT database_names.database_name
        FROM additionaltech_databases AS atd
        LEFT JOIN database_names ON atd.database_id = database_names.database_id
        WHERE atd.candidate_id = %s
    """, (candidate_id,))
    database_row = cursor.fetchall()
    database_list = [db[0] for db in database_row]

    # Query for additionalTech_devops
    cursor.execute("""
        SELECT devops.devop_name
        FROM additionaltech_devops AS atdev
        LEFT JOIN devops ON atdev.devop_id = devops.devop_id
        WHERE atdev.candidate_id = %s
    """, (candidate_id,))
    devops_row = cursor.fetchall()
    devops_list = [dev[0] for dev in devops_row]

    # Combine all the lists into one
    all_technologies = [language_list, framework_list, database_list, devops_list]

    # Flatten the nested lists and filter out empty strings
    tech_list = ", ".join(filter(None, [tech for sublist in all_technologies for tech in sublist]))
    formatted_tech_list = f"\\resumeItem{{{tech_list}}}"




    internal_cv_content = f"""
    \\documentclass[a4paper,12pt]{{article}}
    \\usepackage[utf8]{{inputenc}}
    \\usepackage{{graphicx}}
    \\usepackage{{verbatim}}

    \\usepackage{{titlesec}}

    \\usepackage{{color}}

    \\usepackage{{enumitem}} 

    \\usepackage{{fancyhdr}}

    \\usepackage{{tabularx}}

    \\usepackage{{latexsym}}

    \\usepackage{{marvosym}}

    \\usepackage{{fullpage}}

    \\usepackage[hidelinks]{{hyperref}}

    \\usepackage[normalem]{{ulem}}

    \\usepackage[english]{{babel}}

    \\input glyphtounicode 
    \\pdfgentounicode=1 
    
    \\usepackage[default]{{sourcesanspro}}
    \\urlstyle{{same}} 
    \\pagestyle{{fancy}} 
    \\fancyhf{{}}
    \\renewcommand{{\\headrulewidth}}{{0in}}
    \\renewcommand{{\\footrulewidth}}{{0in}} 
    \\setlength{{\\tabcolsep}}{{0in}}
    \\addtolength{{\\oddsidemargin}}{{-0.5in}}
    \\addtolength{{\\topmargin}}{{-0.5in}}
    \\addtolength{{\\textwidth}}{{1.0in}}
    \\addtolength{{\\textheight}}{{1.0in}}
    \\raggedbottom{{}}
    \\raggedright{{}}
    \\titleformat{{\\section}}
      {{\\large}}{{}}
        {{0em}}{{\\color{{blue}}}}[\\color{{black}}\\titlerule\\vspace{{0pt}}]
    \\renewcommand\\labelitemii{{$\\vcenter{{\\hbox{{\\tiny$\\bullet$}}}}$}}
    \\newcommand{{\\resumeItem}}[1]{{
      \\item\\small{{#1}}
    }}
    \\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[rightmargin=0.15in]}}
    \\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}}}
    \\newcommand{{\\resumeSectionType}}[3]{{
      \\item\\begin{{tabular*}}{{0.96\\textwidth}}[t]{{
        p{{0.24\\linewidth}}p{{0.03\\linewidth}}p{{0.81\\linewidth}}
      }}
        \\textbf{{#1}} & #2 & #3
      \\end{{tabular*}}\\vspace{{-2pt}}
    }}
    \\newcommand{{\\resumeTrioHeading}}[3]{{
      \\item\\small{{
        \\begin{{tabular*}}{{0.96\\textwidth}}[t]{{
          l@{{\\extracolsep{{\\fill}}}}c@{{\\extracolsep{{\\fill}}}}r
        }}
          \\textbf{{#1}} & \\textit{{#2}} & #3
        \\end{{tabular*}}
      }}
    }}
    \\newcommand{{\\resumeQuadHeading}}[4]{{
      \\item
      \\begin{{tabular*}}{{0.96\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
        \\textbf{{#1}} & #2 \\\\
        \\textit{{#3}} & #4 \\\\
      \\end{{tabular*}}
    }}
    \\newcommand{{\\resumeQuadHeadingChild}}[2]{{
      \\item
      \\begin{{tabular*}}{{0.96\\\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
        \\textbf{{\\small#1}} & {{\\small#2}} \\\\
      \\end{{tabular*}}
    }}
    \\newcommand{{\\resumeHeadingListStart}}{{
      \\begin{{itemize}}[leftmargin=0.15in, label={{}}]
    }}
    \\newcommand{{\\resumeHeadingListEnd}}{{\\end{{itemize}}}}
    \\begin{{document}}
    \\hfill
    \\includegraphics[height=1.5cm]{{{logo_file_path}}}
    \\section{{Contact Information}}
      \\resumeHeadingListStart{{}}
        \\resumeSectionType{{Full name}}{{}} {{{full_name}}}
        \\resumeSectionType{{Professional title}}{{}} {{{professional_title}}}
        \\resumeSectionType{{Location}}{{}} {{{location}}}
      \\resumeHeadingListEnd{{}}
    \\section{{Education}}
      \\resumeHeadingListStart{{}}
        \\resumeQuadHeading {{{institute}}}{{{start_date}}}
        {{{degree_name}}}{{{end_date}}}
      \\resumeHeadingListEnd{{}}
      """

    languages_content = ""
    framework_content = ""
    database_content = ""
    devops_content = ""

    if languages:
        languages_content = f"\\resumeSectionType{{Languages}}{{}} {{{languages}}}"

    if framework:
        framework_content = f"\\resumeSectionType{{Frameworks}}{{}} {{{framework}}}"

    if database_name:
        database_content = f"\\resumeSectionType{{Databases}}{{}} {{{database_name}}}"

    if devops:
        devops_content = f"\\resumeSectionType{{DevOps}}{{}} {{{devops}}}"

    internal_cv_content += f"""
    \\section{{Key Skills and Qualifications}}
      \\resumeHeadingListStart{{}}
        {languages_content}
        {framework_content}
        {database_content}
        {devops_content}
      \\resumeHeadingListEnd{{}}
    """

    internal_cv_content += f""" 
    \\section{{Professional (years of) Experience}}
    \\resumeHeadingListStart{{}}
      {experience_content}
       \\resumeHeadingListEnd{{}}
    """

    # Include the Projects section if there is content
    if projects_content:
        internal_cv_content += f"""
    \\section{{Projects}}
      \\resumeHeadingListStart{{}}
        {projects_content}
         \\resumeHeadingListEnd{{}}
    """

    # Include the Other Technologies section if there is content
    if tech_list:
        internal_cv_content += f"""
    \\section{{Other Technologies Used}}
    \\resumeHeadingListStart{{}}
    \\resumeItemListStart{{}}
     {{{formatted_tech_list}}}
    \\resumeItemListEnd{{}}{{\\item}}  # Add a dummy item if needed
    \\resumeHeadingListEnd{{}}
    """
        internal_cv_content += f"""
    \\section{{Additional Candidate Information}}
    \\resumeHeadingListStart{{}}
    \\resumeSectionType {{Phone number}}{{}}{{{phone_number}}}
    \\resumeSectionType {{Email}}{{}} {{{email}}}
    \\resumeSectionType {{Experience years}}{{}}{{{experience_years}}}
    \\resumeSectionType {{Technical rating}}{{}} {{{technical_rating}}}
    \\resumeSectionType {{Non technical rating}}{{}}{{{nontechnical_rating}}}
    \\resumeSectionType {{Minimum salary expectation}}{{}}{{{minimum_salary_expectation}}}
    \\resumeSectionType {{Last cv update}}{{}}{{{last_cv_update}}}
    \\resumeSectionType {{Additional notes}}{{}} {{{additional_notes}}}
\\resumeHeadingListEnd{{}}
   """
    internal_cv_content += f"""
    \\rfoot{{\\hfill
    DEJ Technology GmbH\\\\
    Zu den Tannen 1a, 18107 Elmenhorst-Lichtenhagen\\\\
    Geschäftsführer Dr. Jonas Flint und Dipl. Wirt.-Inf. Erik Heidenreich}}
    \\end{{document}}
    """
    return internal_cv_content


def write_to_tex_file(full_name, cv_content):
    tex_file_name = f"{full_name.replace(' ', '_')}_cv.tex"
    with open(tex_file_name, 'w', encoding="utf-8") as f:
        f.write(cv_content)


def write_to_tex_file_internal(full_name, internal_cv_content):
    tex_file_name = f"{full_name.replace(' ', '_')}_internal_cv.tex"
    with open(tex_file_name, 'w', encoding="utf-8") as f:
        f.write(internal_cv_content)


def compile_pdf(tex_file_name):
    subprocess.run(['pdflatex', tex_file_name])


@app.get("/")
async def root():
    # Connect to the database
    db_connection = connect_to_database()

    # Close the database connection
    db_connection.close()

    # Return a response
    return {"message": "database connected"}


@app.get("/candidates")
def list_all_cvs():
    cnx = connect_to_database()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM candidates")

    candidates_list = []
    for row in cursor.fetchall():
        candidate_info = {"id": row[0], "name": row[1]}
        candidates_list.append(candidate_info)

    cursor.close()
    cnx.close()

    # Check if there are no candidates
    if not candidates_list:
        return JSONResponse(content={"message": "No candidates found"}, status_code=404)

    return {"candidates": candidates_list}


# New endpoint to get TeX content for a candidate
@app.get("/tex/{candidate_id}")
async def get_tex_content(candidate_id: int):
    try:
        cnx = connect_to_database()
        cursor = cnx.cursor()

        candidate_row, education_row, experience_row, projects_row = get_person_cv_by_id(candidate_id, cursor)

        if not candidate_row:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Extract necessary details from the rows for generating CV content
        logo_file_path = os.path.abspath("assets/logopic.png")
        candidate_id = candidate_row[0][0]
        full_name = candidate_row[0][1]
        professional_title = candidate_row[0][2]
        location = candidate_row[0][3]
        institute = education_row[0][0]
        degree_name = education_row[0][1]
        start_date = education_row[0][2]
        end_date = education_row[0][3]

        # Snippet for 'experience_content' variable
        experience_content = ""

        for entry in experience_row:
            job_title, company, start_date, end_date, tasks, candidate_id = entry

            formatted_end_date = 'Present' if end_date.strftime('%Y-%m-%d') == '9999-01-01' else end_date.strftime(
                '%Y-%m-%d')

            tasks_list = tasks.split('*')
            formatted_tasks = "\n".join(
                [f"\\resumeItem{{{desc.strip()}}}" for desc in tasks_list if desc.strip()]
            )
            escape_percentage = '{{\\%}}'
            formatted_tasks = formatted_tasks.replace('%', escape_percentage)

            experience_content += (
                f"  \\resumeQuadHeading{{{job_title}}}{{{start_date}}}{{{company}}}{{{formatted_end_date}}}\n"
                f"    \\resumeItemListStart{{}}\n"
                f"      {formatted_tasks}\n"
                f"    \\resumeItemListEnd{{}}\n"
            )

        # Snippet for 'projects_content' variable
        projects_content = ""
        for project in projects_row:
            project_title = project[0]
            project_description = project[1]
            formatted_project_description = "\n".join(
                [f"\\resumeItem{{{desc.strip()}}}" for desc in project_description.split('*')])
            escape_percentage = '{{\\%}}'
            formatted_project_description = formatted_project_description.replace('%', escape_percentage)
            projects_content += (f"\\resumeTrioHeading{{{project_title}}}{{}}{{}}\n\\resumeItemListStart{{}}"
                                 f"\n{formatted_project_description}\n\\resumeItemListEnd{{}}\n")


        # Generate CV content for clients
        cv_content = generate_cv_content(cursor, candidate_id, full_name, professional_title,
                                         location, institute, degree_name, start_date, end_date,
                                         experience_content, projects_content, logo_file_path)

        # Write CV content to .tex file
        write_to_tex_file(full_name, cv_content)

        # Return the TeX content as response
        with open(f"{full_name.replace(' ', '_')}_cv.tex", 'r', encoding="utf-8") as tex_file:
            tex_content = tex_file.read()

        # Close database connection
        cnx.close()

        return PlainTextResponse(content=tex_content, media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to get TeX content and compile PDF for a candidate

@app.get("/pdf/{candidate_id}")
async def get_pdf_content(candidate_id: int):
        try:
            cnx = connect_to_database()
            cursor = cnx.cursor()

            candidate_row, education_row, experience_row, projects_row = get_person_cv_by_id(candidate_id, cursor)

            if not candidate_row:
                raise HTTPException(status_code=404, detail="Candidate not found")

            # Extract necessary details from the rows for generating CV content
            logo_file_path = os.path.abspath("assets/logopic.png")
            candidate_id = candidate_row[0][0]
            full_name = candidate_row[0][1]
            professional_title = candidate_row[0][2]
            location = candidate_row[0][3]
            institute = education_row[0][0]
            degree_name = education_row[0][1]
            start_date = education_row[0][2]
            end_date = education_row[0][3]

            # Snippet for 'experience_content' variable
            experience_content = ""

            for entry in experience_row:
                job_title, company, start_date, end_date, tasks, candidate_id = entry

                formatted_end_date = 'Present' if end_date.strftime('%Y-%m-%d') == '9999-01-01' else end_date.strftime(
                    '%Y-%m-%d')

                tasks_list = tasks.split('*')
                formatted_tasks = "\n".join(
                    [f"\\resumeItem{{{desc.strip()}}}" for desc in tasks_list if desc.strip()]
                )

                escape_percentage = '{{\\%}}'
                formatted_tasks = formatted_tasks.replace('%', escape_percentage)
                experience_content += (
                    f"  \\resumeQuadHeading{{{job_title}}}{{{start_date}}}{{{company}}}{{{formatted_end_date}}}\n"
                    f"    \\resumeItemListStart{{}}\n"
                    f"      {formatted_tasks}\n"
                    f"    \\resumeItemListEnd{{}}\n"
                )

            # Snippet for 'projects_content' variable
            projects_content = ""
            for project in projects_row:
                project_title = project[0]
                project_description = project[1]
                formatted_project_description = "\n".join(
                    [f"\\resumeItem{{{desc.strip()}}}" for desc in project_description.split('*')])
                escape_percentage = '{{\\%}}'
                formatted_project_description = formatted_project_description.replace('%', escape_percentage)
                projects_content += (f"\\resumeTrioHeading{{{project_title}}}{{}}{{}}\n\\resumeItemListStart{{}}"
                                     f"\n{formatted_project_description}\n\\resumeItemListEnd{{}}\n")


            # Generate CV content for clients
            cv_content = generate_cv_content(cursor, candidate_id, full_name, professional_title,
                                             location, institute, degree_name, start_date, end_date,
                                             experience_content, projects_content, logo_file_path)

            # Write CV content to .tex file
            write_to_tex_file(full_name, cv_content)

            # Compile PDF using pdflatex
            tex_filename = f"{full_name.replace(' ', '_')}_cv.tex"
            pdf_filename = f"{full_name.replace(' ', '_')}_cv.pdf"

            # Run pdflatex command
            subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename])

            # Check if PDF compilation was successful
            if not os.path.exists(pdf_filename):
                raise HTTPException(status_code=500, detail="PDF compilation failed")

            # Return the PDF file as response
            with open(pdf_filename, 'rb') as pdf_file:
                pdf_content = pdf_file.read()

            # Close database connection
            cnx.close()

            return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# New endpoint to get TeX content and compile PDF for a candidate with full_name, for clients
@app.get("/client-cv/{full_name}")
async def get_pdf_content_by_name(full_name: str):
        try:
                cnx = connect_to_database()
                cursor = cnx.cursor()

                candidate_row, education_row, experience_row, projects_row = get_person_cv_by_name(full_name, cursor)

                if None in (candidate_row, education_row, experience_row, projects_row):
                    raise HTTPException(status_code=404, detail="Candidate not found")

                # Extract necessary details from the rows for generating CV content
                logo_file_path = os.path.abspath("assets/logopic.png")
                candidate_id = candidate_row[0][0]
                full_name = candidate_row[0][1]
                professional_title = candidate_row[0][2]
                location = candidate_row[0][3]
                institute = education_row[0][0]
                degree_name = education_row[0][1]
                start_date = education_row[0][2]
                end_date = education_row[0][3]

                # Snippet for 'experience_content' variable
                experience_content = ""

                for entry in experience_row:
                    job_title, company, start_date, end_date, tasks, candidate_id = entry

                    formatted_end_date = 'Present' if end_date.strftime(
                        '%Y-%m-%d') == '9999-01-01' else end_date.strftime(
                        '%Y-%m-%d')

                    tasks_list = tasks.split('*')
                    formatted_tasks = "\n".join(
                        [f"\\resumeItem{{{desc.strip()}}}" for desc in tasks_list if desc.strip()]
                    )

                    escape_percentage = '{{\\%}}'
                    formatted_tasks = formatted_tasks.replace('%', escape_percentage)
                    experience_content += (
                        f"  \\resumeQuadHeading{{{job_title}}}{{{start_date}}}{{{company}}}{{{formatted_end_date}}}\n"
                        f"    \\resumeItemListStart{{}}\n"
                        f"      {formatted_tasks}\n"
                        f"    \\resumeItemListEnd{{}}\n"
                    )

                # Snippet for 'projects_content' variable
                projects_content = ""
                for project in projects_row:
                    project_title = project[0]
                    project_description = project[1]
                    formatted_project_description = "\n".join(
                        [f"\\resumeItem{{{desc.strip()}}}" for desc in project_description.split('*')])
                    escape_percentage = '{{\\%}}'
                    formatted_project_description = formatted_project_description.replace('%', escape_percentage)
                    projects_content += (f"\\resumeTrioHeading{{{project_title}}}{{}}{{}}\n\\resumeItemListStart{{}}"
                                         f"\n{formatted_project_description}\n\\resumeItemListEnd{{}}\n")

                # Generate CV content for clients
                cv_content = generate_cv_content(cursor, candidate_id, full_name, professional_title,
                                                 location, institute, degree_name, start_date, end_date,
                                                 experience_content, projects_content, logo_file_path)

                # Write CV content to .tex file
                write_to_tex_file(full_name, cv_content)

                # Compile PDF using pdflatex
                tex_filename = f"{full_name.replace(' ', '_')}_cv.tex"
                pdf_filename = f"{full_name.replace(' ', '_')}_cv.pdf"

                # Run pdflatex command
                subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename])

                # Check if PDF compilation was successful
                if not os.path.exists(pdf_filename):
                    raise HTTPException(status_code=500, detail="PDF compilation failed")
                # Check if logo file exists
                if not os.path.exists(logo_file_path):
                    raise HTTPException(status_code=500, detail="Logo file not found")

                # Return the PDF file as response
                with open(pdf_filename, 'rb') as pdf_file:
                    pdf_content = pdf_file.read()

                # Close database connection
                cnx.close()

                return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf")

        except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


# New endpoint to get TeX content and compile PDF for a candidate with full_name, for internal use
@app.get("/internal-cv/{full_name}")
async def get_pdf_internal_cv(full_name: str):
        try:
                cnx = connect_to_database()
                cursor = cnx.cursor()

                candidate_row, education_row, experience_row, projects_row = get_person_cv_by_name(full_name, cursor)

                if None in (candidate_row, education_row, experience_row, projects_row):
                    raise HTTPException(status_code=404, detail="Candidate not found")

                # Extract necessary details from the rows for generating CV content
                logo_file_path = os.path.abspath("assets/logopic.png")
                candidate_id = candidate_row[0][0]
                full_name = candidate_row[0][1]
                professional_title = candidate_row[0][2]
                location = candidate_row[0][3]
                phone_number = candidate_row[0][4]
                email = candidate_row[0][5]
                experience_years = candidate_row[0][6]
                technical_rating = candidate_row[0][7]
                nontechnical_rating = candidate_row[0][8]
                minimum_salary_expectation = candidate_row[0][9]
                last_cv_update = candidate_row[0][10]
                additional_notes = candidate_row[0][11]
                institute = education_row[0][0]
                degree_name = education_row[0][1]
                start_date = education_row[0][2]
                end_date = education_row[0][3]

                # Snippet for 'experience_content' variable
                experience_content = ""

                for entry in experience_row:
                    job_title, company, start_date, end_date, tasks, candidate_id = entry

                    formatted_end_date = 'Present' if end_date.strftime(
                        '%Y-%m-%d') == '9999-01-01' else end_date.strftime(
                        '%Y-%m-%d')

                    tasks_list = tasks.split('*')
                    formatted_tasks = "\n".join(
                        [f"\\resumeItem{{{desc.strip()}}}" for desc in tasks_list if desc.strip()]
                    )

                    escape_percentage = '{{\\%}}'
                    formatted_tasks = formatted_tasks.replace('%', escape_percentage)
                    experience_content += (
                        f"  \\resumeQuadHeading{{{job_title}}}{{{start_date}}}{{{company}}}{{{formatted_end_date}}}\n"
                        f"    \\resumeItemListStart{{}}\n"
                        f"      {formatted_tasks}\n"
                        f"    \\resumeItemListEnd{{}}\n"
                    )

                # Snippet for 'projects_content' variable
                projects_content = ""
                for project in projects_row:
                    project_title = project[0]
                    project_description = project[1]
                    formatted_project_description = "\n".join(
                        [f"\\resumeItem{{{desc.strip()}}}" for desc in project_description.split('*')])
                    escape_percentage = '{{\\%}}'
                    formatted_project_description = formatted_project_description.replace('%', escape_percentage)
                    projects_content += (f"\\resumeTrioHeading{{{project_title}}}{{}}{{}}\n\\resumeItemListStart{{}}"
                                         f"\n{formatted_project_description}\n\\resumeItemListEnd{{}}\n")

                # Generate internal CV content and compile PDF...
                internal_cv_content = generate_internal_cv_content(cursor, candidate_id, full_name,professional_title,
                                                                   location, phone_number, email, experience_years, technical_rating,
                                                                       nontechnical_rating,
                                                                       minimum_salary_expectation, last_cv_update,
                                                                       additional_notes, institute, degree_name,
                                                                       start_date,
                                                                       end_date, experience_content, projects_content,
                                                                       logo_file_path)

                # Write internal_CV content to .tex file
                write_to_tex_file_internal(full_name, internal_cv_content)

                # Compile PDF using pdflatex
                internal_tex_filename = f"{full_name.replace(' ', '_')}_internal_cv.tex"
                internal_pdf_filename = f"{full_name.replace(' ', '_')}_internal_cv.pdf"

                # Run pdflatex command
                subprocess.run(["pdflatex", "-interaction=nonstopmode", internal_tex_filename])

                # Check if PDF compilation was successful
                if not os.path.exists(internal_pdf_filename):
                    raise HTTPException(status_code=500, detail="PDF compilation failed")
                # Check if logo file exists
                if not os.path.exists(logo_file_path):
                    raise HTTPException(status_code=500, detail="Logo file not found")

                # Return the PDF file as response
                with open(internal_pdf_filename, 'rb') as pdf_file:
                    pdf_content = pdf_file.read()

                # Close database connection
                cnx.close()

                return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf")

        except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

