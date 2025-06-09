import spacy
import re
    
nlp = spacy.load("en_core_web_sm")   # Load the English NLP model 

def Extract_filter(transcript):
    data = nlp(transcript.lower())

    Filters = {
        'title' : "",
        'location' : "",
        'salary' : "",
        # 'experience' : ""
    }

    for ent in data.ents:
        if ent.label_ == 'GPE':
            Filters['location'] = ent.text
    
    if 'remote' in transcript or 'work from home' in transcript or 'Remote' in transcript:
        Filters['location'] = 'Remote'
        
    
    Salary_pattern = re.search(r'(\d+(\.\d+)?)(\s*-\s*(\d+(\.\d+)?))?\s*(lpa|lakhs|k|thousand)?',transcript)
    if Salary_pattern:
        Filters['salary'] = Salary_pattern.group(0)


    # for job title we have to make a list from which we can match the job title
    job_titles = ['Software Engineer', 'Data Scientist', 'Web Developer', 'ML Engineer', 
                  'DevOps Engineer', 'Full Stack Developer', 'Backend Developer', 'Frontend Developer',
                  'Data Analyst','AI-Engineer','Product Manager', 'Project Manager','UI/UX','UI/UX Designer'
                  'Business Analyst', 'System Administrator', 'Network Engineer', 'Database Administrator',
                  'Cybersecurity Analyst', 'Cloud Engineer', 'Mobile App Developer', 'Game Developer',
                  'Research Scientist', 'Technical Writer', 'Quality Assurance Engineer',
                  'Sales Engineer', 'Marketing Specialist', 'Content Writer', 'Graphic Designer',
                  'SEO Specialist', 'Social Media Manager', 'Customer Support Specialist',
                  'Human Resources Manager', 'Financial Analyst', 'Accountant', 'Operations Manager']
    
    for jtitle in job_titles:
        if jtitle.lower() in transcript.lower():
            Filters['title'] = jtitle
            break

    # if 'fresher' in transcript:
    #     Filters['experience'] = 'fresher'
    # else :
    #     Experience_pattern = re.search(r'(\d+)\s*\+?\s*(years?|yrs?|months?|mos?)',transcript)
    #     if Experience_pattern:
    #        Filters['experience'] = Experience_pattern.group(0)
    
    return Filters
