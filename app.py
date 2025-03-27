from flask import Flask, request, jsonify
from jobspy import scrape_jobs

app = Flask(__name__)

@app.route('/scrape_jobs', methods=['GET'])
def scrape_jobs_api():
    try:
        search_terms = request.args.get("search_term", "software engineer").split(",")
        location = request.args.get("location", "San Francisco, CA")
        results_wanted = int(request.args.get("results_wanted", 2))
        hours_old = int(request.args.get("hours_old", 72))
        country_indeed = request.args.get("location", "USA")
        
        all_jobs = []
        
        for term in search_terms:
            params = {
                "site_name": ["indeed", "linkedin", "zip_recruiter", "google", "bayt"],
                "search_term": term.strip(),
                "google_search_term": term.strip(),
                "location": location,
                "results_wanted": results_wanted,
                "hours_old": hours_old,
                "country_indeed": country_indeed,
            }
            
            jobs = scrape_jobs(**params)
            all_jobs.extend(jobs.to_dict(orient='records'))
        
        return jsonify({"status": "success", "results": len(all_jobs), "jobs": all_jobs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
