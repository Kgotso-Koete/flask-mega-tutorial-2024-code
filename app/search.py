from flask import current_app
from elasticsearch.exceptions import ConnectionError, ConnectionTimeout, NotFoundError
import logging

def ensure_index_exists(index):
    """Create index if it doesn't exist"""
    if not current_app.elasticsearch:
        return False
    
    try:
        if not current_app.elasticsearch.indices.exists(index=index):
            # Create index with basic mapping
            current_app.elasticsearch.indices.create(
                index=index,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "body": {"type": "text"}
                        }
                    }
                }
            )
            current_app.logger.info(f'Created Elasticsearch index: {index}')
        return True
    except Exception as e:
        current_app.logger.error(f'Error ensuring index {index} exists: {e}')
        return False

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    
    # Ensure index exists before trying to add documents
    if not ensure_index_exists(index):
        return
    
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    
    try:
        current_app.elasticsearch.index(index=index, id=model.id, document=payload)
    except ConnectionTimeout as e:
        current_app.logger.error(f'Elasticsearch timeout while indexing {index}/{model.id}: {e}')
    except ConnectionError as e:
        current_app.logger.error(f'Elasticsearch connection error while indexing {index}/{model.id}: {e}')
    except Exception as e:
        current_app.logger.error(f'Elasticsearch error while indexing {index}/{model.id}: {e}')

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    
    try:
        current_app.elasticsearch.delete(index=index, id=model.id)
    except NotFoundError:
        # Document doesn't exist, which is fine for deletion
        pass
    except ConnectionTimeout as e:
        current_app.logger.error(f'Elasticsearch timeout while deleting {index}/{model.id}: {e}')
    except ConnectionError as e:
        current_app.logger.error(f'Elasticsearch connection error while deleting {index}/{model.id}: {e}')
    except Exception as e:
        current_app.logger.error(f'Elasticsearch error while deleting {index}/{model.id}: {e}')

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    
    try:
        # Don't try to create index during search - it should already exist
        search_body = {
            'query': {
                'multi_match': {
                    'query': query, 
                    'fields': ['*']
                }
            },
            'from': (page - 1) * per_page,
            'size': per_page
        }
        
        search = current_app.elasticsearch.search(
            index=index,
            body=search_body
        )
        
        ids = [int(hit['_id']) for hit in search['hits']['hits']]
        total = search['hits']['total']['value']
        return ids, total
        
    except Exception as e:
        # If index doesn't exist, try to create it
        if "index_not_found_exception" in str(e):
            current_app.logger.info(f'Index {index} not found, creating it...')
            if ensure_index_exists(index):
                # Try search again after creating index
                try:
                    search = current_app.elasticsearch.search(
                        index=index,
                        body=search_body
                    )
                    ids = [int(hit['_id']) for hit in search['hits']['hits']]
                    total = search['hits']['total']['value']
                    return ids, total
                except Exception as retry_e:
                    current_app.logger.error(f'Elasticsearch error on retry {index}: {retry_e}')
                    return [], 0
        
        current_app.logger.error(f'Elasticsearch error while querying {index}: {e}')
        return [], 0