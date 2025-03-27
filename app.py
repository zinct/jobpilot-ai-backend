import flask
from flask import Flask, request, jsonify
from jobspy import scrape_jobs
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import traceback
import sys
from fuzzywuzzy import fuzz

app = Flask(__name__)

def safe_lower(value):
    """Safely convert value to lowercase string."""
    if isinstance(value, str):
        return value.lower()
    return ""

def fuzzy_match(text1, text2, threshold=80):
    """Perform fuzzy matching and return True if similarity is above threshold."""
    if text1 and text2:
        score = fuzz.partial_ratio(safe_lower(text1), safe_lower(text2))
        return score >= threshold
    return False

def calculate_match_score(job, user_params):
    print("-----------------------------------------")
    """
    Calculate match score between job and user preferences.
    Handles potential None/NaN values more robustly.
    """
    try:
        score = 0
        
        # Ensure text fields are strings and handle None/NaN
        text_fields = [
            str(job.get(field, "")).lower() if job.get(field) not in [None, np.nan] 
            else "" for field in ["title", "description", "location", "job_type"]
        ]

        # print("job_data", text_fields)

        # Prepare user text for matching
        user_text = " ".join(
            [user_params.get("job_roles", "")] +
            [user_params.get("location", "")] +
            [user_params.get("years_of_experience", "")] +
            [user_params.get("job_level", "")] +
            [user_params.get("work_mode", "")]
        ).lower()

        # print("user_data", user_text)
        
        # Only perform text matching if we have non-empty text
        if user_text and any(text_fields):
            vectorizer = TfidfVectorizer()
            full_text = text_fields + [user_text]
            vectors = vectorizer.fit_transform(full_text)
            similarity_score = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
            score += np.mean(similarity_score) * 500

        # print("base score", score)
        
        # Fuzzy Matching on Job Title
        if fuzzy_match(job.get("title", ""), user_params.get("job_roles", "")):
            score += 20

        if fuzzy_match(job.get("description", ""), user_params.get("education_level", "")):
            score += 20

        # Fuzzy Matching on Job Level
        if fuzzy_match(job.get("job_type", ""), user_params.get("job_level", "")) | fuzzy_match(job.get("description", ""), user_params.get("job_type", "")):
            score += 15

        # Fuzzy Matching on Location
        user_location = user_params.get("location", "")
        if fuzzy_match(job.get("location", ""), user_params.get("location")):
            score += 20

        # Additional rules
        if job.get("is_remote") and user_params.get("work_mode", "").lower() == "remote":
            score += 15

        # print("added score", score)
        # print("last score", round(score))
        
        return min(100, round(score))
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in calculate_match_score: {e}")
        print(traceback.format_exc())
        return 50  # Default score if calculation fails

@app.route('/jobs-recommendation', methods=['GET'])
def scrape_jobs_api():
    try:
        # Validate and parse input parameters with defaults
        search_terms = request.args.get("job_roles", "").split(",")
        
        all_jobs = []

        print("user", {
                "years_of_experience": request.args.get("years_of_experience", ""),
                "job_level": request.args.get("job_level", ""),
                "work_mode": request.args.get("work_mode", ""),
                "company_size": request.args.get("company_size", ""),
                "education_level": request.args.get("education_level", ""),
                "location": request.args.get("location", ""),
                "industries_of_interest": request.args.get("industries_of_interest", ""),
                "personality_traits": request.args.get("personality_traits", ""),
                "job_roles":  request.args.get("job_roles", ""),
            })
        
        for term in search_terms:
            user_params = {
                "years_of_experience": request.args.get("years_of_experience", ""),
                "job_level": request.args.get("job_level", ""),
                "work_mode": request.args.get("work_mode", ""),
                "company_size": request.args.get("company_size", ""),
                "education_level": request.args.get("education_level", ""),
                "location": request.args.get("location", ""),
                "industries_of_interest": request.args.get("industries_of_interest", ""),
                "personality_traits": request.args.get("personality_traits", ""),
                "job_roles": term.strip(),
            }
            
            params = {
                "site_name": ["indeed", "linkedin", "zip_recruiter", "google"],
                "search_term": term.strip(),
                "google_search_term": term.strip(),
                "location": request.args.get("location"),
                "country_indeed": request.args.get("location"),
                "results_wanted": 2,
                "hours_old": 120,
            }

            
            try:
                jobs = scrape_jobs(**params)
                job_list = jobs.to_dict(orient='records') if jobs is not None else []
            except Exception as scrape_error:
                print(f"Job scraping error for term {term}: {scrape_error}")
                print(traceback.format_exc())
                job_list = []
            
            for job in job_list:
                job["match_score"] = calculate_match_score(job, user_params)
                all_jobs.append(job)
        
        return jsonify({
            "status": "success", 
            "results": len(all_jobs), 
            "jobs": all_jobs
        })
    
    except Exception as e:
        # Detailed error tracking
        error_type, error_instance, error_traceback = sys.exc_info()
        line_number = error_traceback.tb_lineno
        filename = error_traceback.tb_frame.f_code.co_filename
        
        error_details = {
            "status": "error",
            "message": str(e),
            "error_type": str(error_type.__name__),
            "line_number": line_number,
            "file": filename,
            "full_traceback": traceback.format_exc()
        }
        
        # Log the full error for server-side debugging
        print("Detailed Error Occurred:")
        print(traceback.format_exc())
        
        return jsonify(error_details), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
