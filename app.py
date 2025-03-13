from flask import Flask, render_template, request, jsonify
import os
from azure.identity import DefaultAzureCredential, AzureDeveloperCliCredential, get_bearer_token_provider
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    ComplexField,
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchIndex
)
from azure.ai.projects import AIProjectClient
from flask import jsonify, request
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects.models import ConnectionType
from openai import AzureOpenAI
from openai.lib.azure import AzureADTokenProvider

app = Flask(__name__, 
    static_folder="static",
    template_folder="api/templates")

scopes = "https://cognitiveservices.azure.com/.default"

tenant_id = os.environ.get('AZURE_TENANT_ID')
credential = DefaultAzureCredential()
# credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
token_provider: AzureADTokenProvider = get_bearer_token_provider(credential, scopes)

search_endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')
openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
project_connection_string=os.environ.get('AZURE_AIPROJECT_CONNECTION_STRING')

index_name = "hotels-quickstart"

# Create a documents payload
documents = [
    {
    "@search.action": "upload",
    "HotelId": "1",
    "HotelName": "Secret Point Motel",
    "Description": "The hotel is ideally located on the main commercial artery of the city in the heart of New York. A few minutes away is Time's Square and the historic centre of the city, as well as other places of interest that make New York one of America's most attractive and cosmopolitan cities.",
    "Description_fr": "L'hôtel est idéalement situé sur la principale artère commerciale de la ville en plein cœur de New York. A quelques minutes se trouve la place du temps et le centre historique de la ville, ainsi que d'autres lieux d'intérêt qui font de New York l'une des villes les plus attractives et cosmopolites de l'Amérique.",
    "Category": "Boutique",
    "Tags": [ "pool", "air conditioning", "concierge" ],
    "ParkingIncluded": "false",
    "LastRenovationDate": "1970-01-18T00:00:00Z",
    "Rating": 3.60,
    "Address": {
        "StreetAddress": "677 5th Ave",
        "City": "New York",
        "StateProvince": "NY",
        "PostalCode": "10022",
        "Country": "USA"
        }
    },
    {
    "@search.action": "upload",
    "HotelId": "2",
    "HotelName": "Twin Dome Motel",
    "Description": "The hotel is situated in a  nineteenth century plaza, which has been expanded and renovated to the highest architectural standards to create a modern, functional and first-class hotel in which art and unique historical elements coexist with the most modern comforts.",
    "Description_fr": "L'hôtel est situé dans une place du XIXe siècle, qui a été agrandie et rénovée aux plus hautes normes architecturales pour créer un hôtel moderne, fonctionnel et de première classe dans lequel l'art et les éléments historiques uniques coexistent avec le confort le plus moderne.",
    "Category": "Boutique",
    "Tags": [ "pool", "free wifi", "concierge" ],
    "ParkingIncluded": "false",
    "LastRenovationDate": "1979-02-18T00:00:00Z",
    "Rating": 3.60,
    "Address": {
        "StreetAddress": "140 University Town Center Dr",
        "City": "Sarasota",
        "StateProvince": "FL",
        "PostalCode": "34243",
        "Country": "USA"
        }
    },
    {
    "@search.action": "upload",
    "HotelId": "3",
    "HotelName": "Triple Landscape Hotel",
    "Description": "The Hotel stands out for its gastronomic excellence under the management of William Dough, who advises on and oversees all of the Hotel's restaurant services.",
    "Description_fr": "L'hôtel est situé dans une place du XIXe siècle, qui a été agrandie et rénovée aux plus hautes normes architecturales pour créer un hôtel moderne, fonctionnel et de première classe dans lequel l'art et les éléments historiques uniques coexistent avec le confort le plus moderne.",
    "Category": "Resort and Spa",
    "Tags": [ "air conditioning", "bar", "continental breakfast" ],
    "ParkingIncluded": "true",
    "LastRenovationDate": "2015-09-20T00:00:00Z",
    "Rating": 4.80,
    "Address": {
        "StreetAddress": "3393 Peachtree Rd",
        "City": "Atlanta",
        "StateProvince": "GA",
        "PostalCode": "30326",
        "Country": "USA"
        }
    },
    {
    "@search.action": "upload",
    "HotelId": "4",
    "HotelName": "Sublime Cliff Hotel",
    "Description": "Sublime Cliff Hotel is located in the heart of the historic center of Sublime in an extremely vibrant and lively area within short walking distance to the sites and landmarks of the city and is surrounded by the extraordinary beauty of churches, buildings, shops and monuments. Sublime Cliff is part of a lovingly restored 1800 palace.",
    "Description_fr": "Le sublime Cliff Hotel est situé au coeur du centre historique de sublime dans un quartier extrêmement animé et vivant, à courte distance de marche des sites et monuments de la ville et est entouré par l'extraordinaire beauté des églises, des bâtiments, des commerces et Monuments. Sublime Cliff fait partie d'un Palace 1800 restauré avec amour.",
    "Category": "Boutique",
    "Tags": [ "concierge", "view", "24-hour front desk service" ],
    "ParkingIncluded": "true",
    "LastRenovationDate": "1960-02-06T00:00:00Z",
    "Rating": 4.60,
    "Address": {
        "StreetAddress": "7400 San Pedro Ave",
        "City": "San Antonio",
        "StateProvince": "TX",
        "PostalCode": "78216",
        "Country": "USA"
        }
    }
]

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

def get_openai_client():
    return AzureOpenAI(
     api_version="2024-06-01",
     azure_endpoint=openai_endpoint,
     azure_ad_token_provider=token_provider,
    )

def get_index_client(hub: bool):
    if not hub:
        return SearchIndexClient(endpoint=search_endpoint, credential=credential)
    
    project = AIProjectClient.from_connection_string(conn_str=project_connection_string, credential=credential)
    search_connection = project.connections.get_default(
        connection_type=ConnectionType.AZURE_AI_SEARCH,
        include_credentials=True)

    index_client = SearchIndexClient(
        endpoint=search_connection.endpoint_url,
        credential=AzureKeyCredential(key=search_connection.key)
    )

    return index_client

def get_search_client(hub: bool):
    if not hub:
        return SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

    project = AIProjectClient.from_connection_string(conn_str=project_connection_string, credential=credential)
    search_connection = project.connections.get_default(
        connection_type=ConnectionType.AZURE_AI_SEARCH,
        include_credentials=True)

    search_client = SearchClient(
        index_name=index_name,
        endpoint=search_connection.endpoint_url,
        credential=AzureKeyCredential(key=search_connection.key)
    )
    return search_client

@app.route('/api/create_index')
def create_index():
    """API endpoint to create search index"""
    use_hub = request.args.get('hub', 'True').lower() == 'true'
    index_client = get_index_client(use_hub)

    fields = [
            SimpleField(name="HotelId", type=SearchFieldDataType.String, key=True),
            SearchableField(name="HotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="Description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="Description_fr", type=SearchFieldDataType.String, analyzer_name="fr.lucene"),
            SearchableField(name="Category", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),

            SearchableField(name="Tags", collection=True, type=SearchFieldDataType.String, facetable=True, filterable=True),

            SimpleField(name="ParkingIncluded", type=SearchFieldDataType.Boolean, facetable=True, filterable=True, sortable=True),
            SimpleField(name="LastRenovationDate", type=SearchFieldDataType.DateTimeOffset, facetable=True, filterable=True, sortable=True),
            SimpleField(name="Rating", type=SearchFieldDataType.Double, facetable=True, filterable=True, sortable=True),

            ComplexField(name="Address", fields=[
                SearchableField(name="StreetAddress", type=SearchFieldDataType.String),
                SearchableField(name="City", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="StateProvince", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="PostalCode", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="Country", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
            ])
        ]

    scoring_profiles = []
    suggester = [{'name': 'sg', 'source_fields': ['Tags', 'Address/City', 'Address/Country']}]

    # Create the search index=
    index = SearchIndex(name=index_name, fields=fields, suggesters=suggester, scoring_profiles=scoring_profiles)
    result = index_client.create_or_update_index(index)
    print(f' {result.name} created')

    return jsonify({"index": result.name, 'credential': type(index_client._credential).__name__})

@app.route('/api/upload_documents')
def upload_documents():
    """API endpoint to upload documents to the index"""
    use_hub = request.args.get('hub', 'True').lower() == 'true'
    search_client = get_search_client(use_hub)
    try:
        result = search_client.upload_documents(documents=documents)
        print("Upload of new document succeeded: {}".format(result[0].succeeded))
        return jsonify({"result": result[0].succeeded, 'credential': type(search_client._credential).__name__})
    except Exception as ex:
        print(ex.message)
        return jsonify({"error": "Upload failed", "message": ex.message, 'credential': type(search_client._credential).__name__}), 500

@app.route('/api/search')
def search():
    """API endpoint to perform search with a query"""
    use_hub = request.args.get('hub', 'True').lower() == 'true'
    search_client = get_search_client(use_hub)

    # Get query parameter from request, default to "*" if not provided
    search_query = request.args.get('query', '*')
    
    # Run a search with the provided query
    results = search_client.search(
        query_type='simple',
        search_text=search_query,
        select='HotelName,Description,Tags',
        include_total_count=True
    )

    response_data = {
        'credential': type(search_client._credential).__name__,
        'total_count': results.get_count(),
        'results': []
    }
    
    for result in results:
        response_data['results'].append({
            'score': result["@search.score"],
            'hotel_name': result["HotelName"],
            'description': result["Description"],
            'tags': result.get("Tags", [])
        })
    
    return jsonify(response_data)

@app.route('/api/empty_query')
def empty_query():
    use_hub = request.args.get('hub', 'True').lower() == 'true'
    search_client = get_search_client(use_hub)

    # Run an empty query (returns selected fields, all documents)
    results = search_client.search(query_type='simple',
        search_text="*",
        select='HotelName,Description',
        include_total_count=True)

    response_data = {
        'credential': type(search_client._credential).__name__,
        'total_count': results.get_count(),
        'results': []
    }
    
    for result in results:
        response_data['results'].append({
            'score': result["@search.score"],
            'hotel_name': result["HotelName"],
            'description': result["Description"]
        })
    
    return jsonify(response_data)

@app.route('/api/recommend')
def recommend():
    """API endpoint to get AI recommendations based on search results"""
    use_hub = request.args.get('hub', 'True').lower() == 'true'
    search_client = get_search_client(use_hub)
    openai_client = get_openai_client()
    
    # Get query parameter from request
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    try:
        # Search for relevant hotels
        search_results = search_client.search(
            search_text=query,
            top=5,
            select="Description,HotelName,Tags"
        )
        search_results = list(search_results)
        
        # Format search results as sources
        sources_formatted = "\n".join([
            f'{document["HotelName"]}:{document["Description"]}:{document.get("Tags", [])}' 
            for document in search_results
        ])

        # Grounding prompt for the OpenAI model
        grounding_prompt = """
        You are a friendly assistant that recommends hotels based on activities and amenities.
        Answer the query using only the sources provided below in a friendly and concise bulleted manner.
        Answer ONLY with the facts listed in the list of sources below.
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below.
        Query: {query}
        Sources:
        {sources}
        """

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": grounding_prompt.format(query=query, sources=sources_formatted)
                }
            ]
        )

        recommendation = response.choices[0].message.content

        return jsonify({
            'recommendation': recommendation,
            'sources_count': len(search_results),
            'credential': type(search_client._credential).__name__
        })

    except Exception as ex:
        return jsonify({
            "error": "Recommendation failed", 
            "message": str(ex),
            'credential': type(search_client._credential).__name__
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
