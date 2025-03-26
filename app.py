import os

from flask import Flask, render_template, request, jsonify
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from openai import AzureOpenAI

app = Flask(__name__, template_folder="templates")

search_endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')
openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')

openai_model_name = "gpt-4o"
index_name = "hotels-quickstart"

credential = DefaultAzureCredential()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/recommend')
def recommend():
    """API endpoint to get AI recommendations based on search results"""
    # Get query parameter from request
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    try:
        sources_formatted = ""        
        search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)
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

        # Grounding prompt
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

        messages = [
            {
            "role": "user",
            "content": grounding_prompt.format(query=query, sources=sources_formatted)
            }
        ]

        openai_client = AzureOpenAI(
            api_version="2024-06-01",
            azure_endpoint=openai_endpoint,
            azure_ad_token_provider=get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default"),
        )
        response = openai_client.chat.completions.create(
            model=openai_model_name,
            messages=messages,
            max_tokens=100,
        )

        recommendation = response.choices[0].message.content

        return jsonify({
            'recommendation': recommendation,
            'sources_count': len(search_results),
        })

    except Exception as ex:
        return jsonify({
            "error": "Recommendation failed", 
            "message": str(ex),
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
