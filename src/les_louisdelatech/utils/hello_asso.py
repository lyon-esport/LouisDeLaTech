"""HelloAsso API helpers.

HelloAsso is used as the "source of truth" for membership payments and form data.
We use it to compare:
- memberships that have been paid (HelloAsso orders)
- users that exist in Google Workspace (Admin SDK)

See commands in `extensions/hello_asso.py`.
"""

BASE_URL = "https://api.helloasso.com/v5"


def get_orders(client, organization_slug: str, form_type: str, form_slug: str):
    """Fetch all orders for a given form.

    HelloAsso endpoints are paginated. We iterate over all pages and return the
    concatenated `data` list.

    Args:
        client: An OAuth2Session (requests-oauthlib) configured with a Bearer token.
        organization_slug: HelloAsso organization slug.
        form_type: e.g. "Membership".
        form_slug: slug portion from the HelloAsso URL.
    """
    results = []
    page_index = 1
    page_count = 1

    while page_index <= page_count:
        resp = client.get(
            f"{BASE_URL}/organizations/{organization_slug}/forms/{form_type}/{form_slug}/orders",
            params={
                "pageIndex": page_index,
                "pageSize": 100,
                "withDetails": True,
            },
        ).json()

        results += resp["data"]
        pagination = resp.get("pagination", {})
        page_count = pagination.get("totalPages", page_count)
        page_index += 1

    return results
