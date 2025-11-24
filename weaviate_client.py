"""
Centralized Weaviate client creation and batch operations.
All scripts use this module for consistent Weaviate operations.
"""


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import weaviate
from weaviate.connect import ConnectionParams
from typing import List, Dict, Any, Optional, Tuple

import config

logger = logging.getLogger(__name__)

# Global session for connection pooling and reuse
_http_session = None


def get_http_session():
    """
    Get or create a requests session with connection pooling and retry logic.
    Reuses connections to avoid 'Connection refused' errors.
    """
    global _http_session
    
    if _http_session is None:
        _http_session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Keep 10 connections alive
            pool_maxsize=20,      # Max pool size
            pool_block=False
        )
        
        _http_session.mount("http://", adapter)
        _http_session.mount("https://", adapter)
        
        # Set keep-alive
        _http_session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=60, max=1000'
        })
        
        logger.info("Created HTTP session with connection pooling and retry logic")
    
    return _http_session


def create_weaviate_client():
    """
    Create and connect to Weaviate client.
    Handles both localhost and remote connections.
    Supports HTTP-only mode (no gRPC).
    
    Returns:
        Connected Weaviate client
    """
    try:
        # Parse URL to extract protocol, host, and port
        url = config.WEAVIATE_URL
        is_https = url.startswith("https://")
        url_without_protocol = url.replace("https://", "").replace("http://", "")
        
        # Split host and port
        if ":" in url_without_protocol:
            host, port_str = url_without_protocol.split(":", 1)
            port_str = port_str.split("/")[0]
            port = int(port_str)
        else:
            host = url_without_protocol.split("/")[0]
            port = 443 if is_https else 80
        
        # Check if authentication is needed
        use_auth = config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key"
        
        logger.info(f"Connecting to Weaviate at {host}:{port} (HTTPS: {is_https}, Auth: {use_auth})")
        
        # Determine if gRPC should be used
        use_grpc = getattr(config, 'WEAVIATE_USE_GRPC', False)
        
        if use_grpc:
            # gRPC enabled
            logger.info(f"  gRPC enabled: {host}:50051")
            import weaviate.classes.init as wvc_init
            client = weaviate.WeaviateClient(
                connection_params=ConnectionParams.from_params(
                    http_host=host,
                    http_port=port,
                    http_secure=is_https,
                    grpc_host=host,
                    grpc_port=50051,
                    grpc_secure=is_https
                ),
                auth_client_secret=weaviate.auth.AuthApiKey(config.WEAVIATE_API_KEY) if use_auth else None,
                skip_init_checks=True,
                additional_config=wvc_init.AdditionalConfig(
                    timeout=wvc_init.Timeout(init=30, query=60, insert=120)
                )
            )
        else:
            # HTTP-only mode (no gRPC)
            logger.info(f"  gRPC disabled (HTTP-only mode)")
            # Must provide different port for validation but won't actually use gRPC
            dummy_grpc_port = port + 1 if port < 65535 else port - 1
            import weaviate.classes.init as wvc_init
            client = weaviate.WeaviateClient(
                connection_params=ConnectionParams.from_params(
                    http_host=host,
                    http_port=port,
                    http_secure=is_https,
                    grpc_host=host,
                    grpc_port=dummy_grpc_port,
                    grpc_secure=False
                ),
                auth_client_secret=weaviate.auth.AuthApiKey(config.WEAVIATE_API_KEY) if use_auth else None,
                skip_init_checks=True,
                additional_config=wvc_init.AdditionalConfig(
                    timeout=wvc_init.Timeout(init=5, query=60, insert=120)  # Short init timeout
                )
            )
        
        try:
            client.connect()
            logger.info(f"✓ Connected to Weaviate at {config.WEAVIATE_URL}")
        except Exception as conn_error:
            logger.warning(f"Connection attempt had issues: {conn_error}")
            logger.info("Client created anyway - REST API operations should still work")
            # Don't raise - client object exists and REST API calls will work
        
        return client
        
    except Exception as e:
        logger.error(f"Failed to create Weaviate client: {e}")
        raise


def batch_insert_objects(objects: List[Dict[str, Any]], collection_name: str = None) -> Tuple[int, int]:
    """
    Insert multiple objects into Weaviate using REST API batch endpoint.
    Uses connection pooling to avoid 'Connection refused' errors.
    
    Args:
        objects: List of objects to insert, each with 'properties' and 'vector'
        collection_name: Collection name (defaults to config.WEAVIATE_CLASS_NAME)
    
    Returns:
        Tuple of (success_count, error_count)
    """
    if collection_name is None:
        collection_name = config.WEAVIATE_CLASS_NAME
    
    success_count = 0
    error_count = 0
    
    try:
        # Prepare batch payload for REST API
        batch_payload = []
        for obj in objects:
            batch_payload.append({
                "class": collection_name,
                "properties": obj['properties'],
                "vector": obj['vector']
            })
        
        if not batch_payload:
            return 0, 0
        
        # Get reusable session with connection pooling
        session = get_http_session()
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
        
        # Send batch insert request using session (reuses connections)
        response = session.post(
            f"{config.WEAVIATE_URL}/v1/batch/objects?consistency_level=ONE",
            headers=headers,
            json={"objects": batch_payload},
            timeout=120
        )
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            # Count successes and errors
            for item in result:
                if item.get("result", {}).get("errors"):
                    error_count += 1
                    logger.error(f"Batch insert error: {item.get('result', {}).get('errors')}")
                else:
                    success_count += 1
            
            # If no explicit errors, assume all succeeded
            if success_count == 0 and error_count == 0:
                success_count = len(batch_payload)
        else:
            logger.error(f"Batch insert failed: {response.status_code} - {response.text}")
            error_count = len(batch_payload)
        
        return success_count, error_count
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error during batch insert: {e}")
        logger.error("This might be due to server overload or network issues")
        logger.error("Suggestion: Reduce MAX_CONCURRENT_EMBEDDINGS or add delay between batches")
        return 0, len(objects)
    except Exception as e:
        logger.error(f"Error during batch insert: {e}")
        return 0, len(objects)


def insert_single_object(properties: Dict[str, Any], vector: List[float], 
                        collection_name: str = None) -> Optional[str]:
    """
    Insert a single object into Weaviate using REST API.
    Uses connection pooling for reliability.
    
    Args:
        properties: Object properties
        vector: Embedding vector
        collection_name: Collection name (defaults to config.WEAVIATE_CLASS_NAME)
    
    Returns:
        Object UUID if successful, None otherwise
    """
    if collection_name is None:
        collection_name = config.WEAVIATE_CLASS_NAME
    
    try:
        # Get reusable session
        session = get_http_session()
        
        headers = {"Content-Type": "application/json"}
        if config.WEAVIATE_API_KEY and config.WEAVIATE_API_KEY != "your-weaviate-api-key":
            headers["Authorization"] = f"Bearer {config.WEAVIATE_API_KEY}"
        
        payload = {
            "class": collection_name,
            "properties": properties,
            "vector": vector
        }
        
        response = session.post(
            f"{config.WEAVIATE_URL}/v1/objects?consistency_level=ONE",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("id")
        else:
            logger.error(f"Insert failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error inserting object: {e}")
        return None


def get_collection(client, collection_name: str = None):
    """
    Get a Weaviate collection.
    
    Args:
        client: Weaviate client
        collection_name: Collection name (defaults to config.WEAVIATE_CLASS_NAME)
    
    Returns:
        Collection object
    """
    if collection_name is None:
        collection_name = config.WEAVIATE_CLASS_NAME
    
    try:
        if not client.collections.exists(collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist. Run create_weaviate_schema.py first.")
        
        return client.collections.get(collection_name)
    except Exception as e:
        logger.error(f"Error getting collection: {e}")
        raise

