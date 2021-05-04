from http.client import responses


def format_discord_name(firstname, lastname, pseudo):
    return f"{firstname.title()} {pseudo} {lastname[:1].upper()}"


def format_gsuite_email(firstname, lastname):
    return f"{firstname.lower()}.{lastname.lower()}@lyon-esport.fr"


def format_google_api_error(error):
    return f"Google API error status code {error.status_code}:{responses[error.status_code]}"
