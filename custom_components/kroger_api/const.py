DOMAIN = "kroger_api"

AUTH_CALLBACK_NAME = "api:kroger:oauth"
AUTH_CALLBACK_URL = "/api/kroger/oauth"

API_BASE_URL = "https://api.kroger.com/v1"

OAUTH2_AUTHORIZE = f"{API_BASE_URL}/oauth2/authorize"
OAUTH2_TOKEN = f"{API_BASE_URL}/connect/oauth2/token"

PRODUCT_SEARCH_URL = f"{API_BASE_URL}/products"
