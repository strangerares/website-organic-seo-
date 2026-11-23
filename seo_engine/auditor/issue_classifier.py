SEVERITY_WEIGHT = {"Critical": 15, "High": 8, "Medium": 4, "Low": 2, "Informational": 1}


def issue(severity, code, description, affected_url, why, recommendation, fix):
    return {
        "severity": severity,
        "code": code,
        "description": description,
        "affected_url": affected_url,
        "why_it_matters": why,
        "recommendation": recommendation,
        "how_to_fix": fix,
    }
