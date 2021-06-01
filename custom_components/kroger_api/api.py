import logging
from typing import cast

from aiohttp import BasicAuth
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    API_BASE_URL
)

_LOGGER = logging.getLogger(__name__)


class ConfigEntryKrogerApiClient:
    """Provide Kroger API authentication tied to an OAuth2 based config entry."""

    def __init__(
            self,
            hass: HomeAssistantType,
            oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Initialize Kroger API auth."""
        self._hass = hass
        self._oauth_session = oauth_session

    async def async_get_access_token(self):
        """Return a valid access token."""
        if not self._oauth_session.valid_token:
            await self._oauth_session.async_ensure_token_valid()

        return self._oauth_session.token["access_token"]

    async def async_query_products(self,
                                   brand: str = None,
                                   term: str = None,
                                   location_id: str = None):
        """Query the Kroger API for products."""
        if not term:
            raise ValueError("Term must be specified when querying products.")

        product_url = f"{API_BASE_URL}/product"
        headers = {
            "Accept": "application/json"
        }
        params = {
            "filter.term": term
        }
        if brand:
            params["filter.brand"] = brand
        if location_id:
            params["filter.locationId"] = location_id

        try:
            product_resp = await self._oauth_session.async_request('GET',
                                                                   product_url,
                                                                   params=params,
                                                                   headers=headers)
            product_resp.raise_for_status()
            json_response = await product_resp.json()
            products = [
                {
                    'upc': item['productId'],
                    'description': item['description'],
                    'brand': item['brand'],
                    'image': [image_data['sizes'][0]['url']
                              for image_data
                              in item['images']
                              if image_data['perspective'] == 'front'][0]
                }
                for item
                in json_response['data']]
            return products
        except Exception as ex:
            _LOGGER.error("Unable to retrieve products: %s",
                          str(ex))
            return None

    async def async_query_locations(self,
                                    zip_code: str = None,
                                    latitude: str = None,
                                    longitude: str = None):
        """Query the Kroger API for locations."""

        location_url = f"{API_BASE_URL}/locations"
        headers = {
            "Accept": "application/json"
        }
        params = {}
        if latitude and longitude:
            params["filter.lat.near"] = latitude
            params["filter.lon.near"] = longitude
        elif zip_code:
            params["filter.zipCode.near"] = zip_code
        else:
            params['filter.lat.near'] = str(self._hass.config.latitude)
            params['filter.lon.near'] = str(self._hass.config.longitude)

        try:
            location_resp = await self._oauth_session.async_request('GET',
                                                                    location_url,
                                                                    params=params,
                                                                    headers=headers)
            location_resp.raise_for_status()
            json_response = await location_resp.json()
            locations = [
                {
                    'locationId': item['locationId'],
                    'name': item['name']
                }
                for item
                in json_response['data']]
            return locations
        except Exception as ex:
            _LOGGER.error("Unable to retrieve locations: %s",
                          str(ex))
            return None

    async def add_to_cart(self,
                          upc: str,
                          quantity: int = 1):
        """Add item to shopping cart."""
        cart_url = f"{API_BASE_URL}/cart/add"
        headers = {
            "Content Type": "application.json",
            "Accept": "application/json"
        }

        data = {
            "upc": upc,
            "quantity": quantity
        }

        try:
            cart_add_resp = await self._oauth_session.async_request('PUT',
                                                                    cart_url,
                                                                    json=data,
                                                                    headers=headers)
            cart_add_resp.raise_for_status()
            await cart_add_resp.json()
            return True
        except Exception as ex:
            _LOGGER.error("Unable to retrieve locations: %s",
                          str(ex))
            return False


class KrogerApiOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Kroger API OAuth2 implementation."""

    @property
    def extra_authorize_data(self) -> dict:
        return {
            'scope': [
                'cart.basic:write',
                "product.compact",
                "locations"
            ]
        }

    async def _token_request(self, data: dict) -> dict:
        """Make a token request."""
        session = async_get_clientsession(self.hass)

        data["client_id"] = self.client_id

        if self.client_secret is not None:
            data["client_secret"] = self.client_secret

        headers = {
            "Authorization": BasicAuth(self.client_id,
                                       self.client_secret).encode(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        resp = await session.post(self.token_url,
                                  headers=headers,
                                  data=data)
        resp.raise_for_status()
        return cast(dict, await resp.json())


class ProductQueryView(HomeAssistantView):
    """Product Query View."""

    requires_auth = False
    url = "/api/kroger/products"
    name = "api:kroger:products"

    def __init__(self,
                 api_client: ConfigEntryKrogerApiClient):
        super(ProductQueryView, self).__init__()
        self._client = api_client

    async def get(self, request: Request) -> Response:
        """Query products."""
        try:
            products = await self._client.async_query_products(term=request.query.get('term'),
                                                               brand=request.query.get('brand'),
                                                               location_id=request.query.get('locationId'))
            return Response(
                content_type="application/json",
                body=products,
                status=200
            )
        except Exception as ex:
            return Response(
                content_type="application/json",
                body={"error": f"Unexpected error occurred: {ex}"},
                status=500
            )


class LocationQueryView(HomeAssistantView):
    """Location Query View."""

    requires_auth = False
    url = "/api/kroger/locations"
    name = "api:kroger:locations"

    def __init__(self,
                 api_client: ConfigEntryKrogerApiClient):
        super(LocationQueryView, self).__init__()
        self._client = api_client

    async def get(self, request: Request) -> Response:
        """Query products."""
        try:
            locations = await self._client.async_query_locations(zip_code=request.query.get('zip_code'),
                                                                 latitude=request.query.get('latitude'),
                                                                 longitude=request.query.get('longitude'))
            return Response(
                content_type="application/json",
                body=locations,
                status=200
            )
        except Exception as ex:
            return Response(
                content_type="application/json",
                body={"error": f"Unexpected error occurred: {ex}"},
                status=500
            )


class AddToCartView(HomeAssistantView):
    """Add to Card View."""

    requires_auth = False
    url = "/api/kroger/cart_add"
    name = "api:kroger:cart_add"

    def __init__(self,
                 api_client: ConfigEntryKrogerApiClient):
        super(AddToCartView, self).__init__()
        self._client = api_client

    async def put(self, request: Request) -> Response:
        """Add item to cart.."""
        try:
            request_json = await request.json()
            await self._client.add_to_cart(upc=request_json.get('upc'),
                                           quantity=request_json.get('quantity', 1))
            return Response(
                content_type="application/json",
                status=200
            )
        except Exception as ex:
            return Response(
                content_type="application/json",
                body={"error": f"Unexpected error occurred: {ex}"},
                status=500
            )
