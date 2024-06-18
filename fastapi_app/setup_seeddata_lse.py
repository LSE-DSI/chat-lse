import asyncio
import json
from dotenv import load_dotenv
from fastapi_app.embeddings import compute_text_embedding  # Ensure correct imports
from fastapi_app.clients import create_embed_client  # Import OpenAI client creation function

async def generate_json_entry(doc_id, type, doc_name, description, link, embed_model):
    try:
        embedding = await compute_text_embedding(
            q=description,
            embed_model=embed_model
        )
        return {
            "Id": doc_id,
            "Type": type,
            "Name": doc_name,
            "Description": description,
            "Link": link,
            "Embedding": embedding
        }
    except Exception as e:
        print(f"Failed to compute embedding for {doc_name}: {e}")
        return None

async def main():
    load_dotenv(override=True)

    embed_model = await create_embed_client()

    # Manually defined descriptions and links for each document
    documents = [
        (1, "PDF","Exam Procedures for Candidates",  "Outlines essential procedures for LSE's in-person exams for the 2023/24 academic year. It details candidate responsibilities, exam conduct rules, permitted materials, use of electronic devices, and protocols for e-Exams, including equipment requirements and emergency procedures, to ensure fairness and integrity during the examination process.", "https://info.lse.ac.uk/current-students/services/assets/documents/Exam-Procedures-for-Candidates.pdf"),
        (2, "PDF","Spring Exam Timetable 2024",  "Detailed exam schedule for LSE's Spring 2024 session, including dates, times, and courses.", "https://info.lse.ac.uk/current-students/services/assets/documents/Spring-Exam-Timetable-2024-Final.pdf"),
        (3, "PDF","Studnet Guidance on Deferrals", "Outlines policies and procedures for students considering deferring exams or coursework. It covers eligibility, application steps, academic impacts, and available support resources to help students navigate the deferral process effectively.", "https://info.lse.ac.uk/current-students/services/assets/documents/Student-Guidance-Deferral.pdf"),
        (4, "PDF","Academic Appeals Regulation",  "This LSE document details the academic appeals procedures for undergraduate and master's students, specifying eligibility, the process, and grounds for appeals, which include procedural errors and new exceptional circumstances", "https://info.lse.ac.uk/current-students/services/assets/documents/Appeals-Regulations.pdf"),
        (5, "PDF","Three Year Classification Scheme For BA/BSc Degrees", "Outlines the classification scheme for BA and BSc degrees starting from the 2018/19 academic year. It details the criteria for awarding marks, eligibility for degree awards, and the specifics of calculating final degree classifications, including considerations for exceptional circumstances and penalties for unredeemed failures.", "https://info.lse.ac.uk/staff/divisions/academic-registrars-division/Teaching-Quality-Assurance-and-Review-Office/Assets/Documents/Calendar/BA-BSc-Three-Year-scheme-for-students-from-2018.19.pdf"),
        (6, "PDF","In-Course Financial Support Application Guide",  "Guide for students applying for in-course financial support. It includes instructions for completing the application form, eligibility criteria, required documentation, and assessment procedures. The guide covers various aspects of financial aid, including allowances for dependents, disability-related costs, and emergency financial needs, aiming to assist students experiencing financial difficulties during their studies.", "https://info.lse.ac.uk/current-students/financial-support/assets/documents/In-Course-Financial-Support.pdf"),
        (7, "PDF","Interruption of Studies Policy",  "Outlines policy for students needing a temporary break from their studies due to personal, professional, or health reasons. It details the conditions under which interruptions are granted, the process for applying, and the implications on academic standing, visa status, and financial commitments. It also covers the return to studies, emphasizing the need for careful planning and communication with academic mentors and departmental staff.", "https://info.lse.ac.uk/Staff/Divisions/Academic-Registrars-Division/Teaching-Quality-Assurance-and-Review-Office/Assets/Documents/Calendar/InterruptionPolicy.pdf"),
        (8, "PDF","Student Complaints Procedure", "Outlines the procedures for handling student complaints, providing a structured approach for lodging and resolving issues related to academic or administrative services. It details the stages of complaint resolution, including early resolution, formal complaint submission, and review processes, ensuring a fair and systematic approach to addressing student grievances.","https://info.lse.ac.uk/staff/services/Policies-and-procedures/Assets/Documents/comPro.pdf")
    ]

    json_data = []
    for doc_id, doc_type, doc_name, description, link in documents:  # corrected unpacking
        json_entry = await generate_json_entry(doc_id, doc_type, doc_name, description, link, embed_model)  # added missing doc_type
        if json_entry:
            json_data.append(json_entry)
        else:
            print(f"Failed to create JSON entry for {doc_name}")

    json_file_path = "fastapi_app/seed_data_lse.json"
    try:
        with open(json_file_path, "w") as f:
            json.dump(json_data, f, indent=4)
        print(f"JSON file created successfully at {json_file_path}")
    except Exception as e:
        print(f"Failed to write JSON file: {e}")
 
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Reuse the existing running loop
        loop.create_task(main())
    else:
        # No running event loop, safe to use asyncio.run
        asyncio.run(main())