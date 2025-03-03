"""Utilities for fetching and processing data from the cryoET API."""
import pandas as pd
from cryoet_data_portal import Client
from cryoet_data_portal import (
    Deposition, 
    Dataset, 
    Run, 
    Tomogram, 
    Annotation, 
    TomogramVoxelSpacing,
    AnnotationShape,
    AnnotationFile
)
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional, Union
from cryoet_data_portal_dashboard.cache import cache
import random  # Add this import at the top of the file
import numpy as np

# Set up logging - Configure this first before any other imports or operations
logging.basicConfig(level=logging.INFO)

# Suppress logs from GraphQL and related libraries
logging.getLogger('gql').setLevel(logging.WARNING)
logging.getLogger('gql.transport').setLevel(logging.WARNING)
logging.getLogger('gql.transport.requests').setLevel(logging.WARNING)
logging.getLogger('gql.dsl').setLevel(logging.WARNING)
logging.getLogger('cryoet_data_portal').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Get a logger for this module
logger = logging.getLogger(__name__)

# Initialize API client
client = Client()

# Base URL for the external data portal
PORTAL_BASE_URL = "https://cryoetdataportal.czscience.com"


def fetch_depositions() -> pd.DataFrame:
    """Fetch all depositions and convert to DataFrame.
    
    Uses the Deposition.find() method to retrieve all depositions from the API.
    
    Returns:
        pd.DataFrame: DataFrame containing all depositions and their attributes.
    """
    logger.info("Fetching depositions data...")
    try:
        depositions = list(Deposition.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([d.to_dict() for d in depositions])
        
        # Convert date strings to datetime objects
        if 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching depositions: {e}")
        return pd.DataFrame()


def fetch_datasets() -> pd.DataFrame:
    """Fetch all datasets and convert to DataFrame.
    
    Uses the Dataset.find() method to retrieve all datasets from the API.
    
    Returns:
        pd.DataFrame: DataFrame containing all datasets and their attributes.
    """
    logger.info("Fetching datasets data...")
    try:
        datasets = list(Dataset.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([d.to_dict() for d in datasets])
        
        # Convert date strings to datetime objects
        if 'release_date' in df.columns:
            df['release_date'] = pd.to_datetime(df['release_date'])
        if 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching datasets: {e}")
        return pd.DataFrame()


def fetch_runs() -> pd.DataFrame:
    """Fetch all runs and convert to DataFrame.
    
    Uses the Run.find() method to retrieve all runs from the API.
    If preloaded data is available in the cache, returns that instead.
    
    Returns:
        pd.DataFrame: DataFrame containing all runs and their attributes.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_runs = cache.get("preloaded_runs")
        if preloaded_runs is not None:
            logger.info("Using preloaded runs data from cache")
            return preloaded_runs
    except ImportError:
        # Cache might not be initialized yet, continue with normal fetching
        pass
    
    logger.info("Fetching runs data from API...")
    try:
        runs = list(Run.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([r.to_dict() for r in runs])
        
        # Convert date strings to datetime objects
        if 'release_date' in df.columns:
            df['release_date'] = pd.to_datetime(df['release_date'])
        if 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching runs: {e}")
        return pd.DataFrame()


def fetch_tomograms() -> pd.DataFrame:
    """Fetch all tomograms and convert to DataFrame.
    
    Uses the Tomogram.find() method to retrieve all tomograms from the API.
    If preloaded data is available in the cache, returns that instead.
    
    Returns:
        pd.DataFrame: DataFrame containing all tomograms and their attributes.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_tomograms = cache.get("preloaded_tomograms")
        if preloaded_tomograms is not None:
            logger.info("Using preloaded tomograms data from cache")
            return preloaded_tomograms
    except ImportError:
        # Cache might not be initialized yet, continue with normal fetching
        pass
    
    logger.info("Fetching tomograms data from API...")
    try:
        tomograms = list(Tomogram.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([t.to_dict() for t in tomograms])
        
        # Convert date strings to datetime objects
        if 'release_date' in df.columns:
            df['release_date'] = pd.to_datetime(df['release_date'])
        if 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching tomograms: {e}")
        return pd.DataFrame()


def fetch_annotations() -> pd.DataFrame:
    """Fetch all annotations and convert to DataFrame.
    
    Uses the Annotation.find() method to retrieve all annotations from the API.
    If preloaded data is available in the cache, returns that instead.
    
    Returns:
        pd.DataFrame: DataFrame containing all annotations and their attributes.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_annotations = cache.get("preloaded_annotations")
        if preloaded_annotations is not None:
            logger.info("Using preloaded annotations data from cache")
            return preloaded_annotations
    except ImportError:
        # Cache might not be initialized yet, continue with normal fetching
        pass
    
    logger.info("Fetching annotations data from API...")
    try:
        annotations = list(Annotation.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([a.to_dict() for a in annotations])
        
        # Convert date strings to datetime objects
        if 'release_date' in df.columns:
            df['release_date'] = pd.to_datetime(df['release_date'])
        if 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching annotations: {e}")
        return pd.DataFrame()


def fetch_tomogram_voxel_spacings() -> pd.DataFrame:
    """Fetch all tomogram voxel spacings and convert to DataFrame.
    
    Uses the TomogramVoxelSpacing.find() method to retrieve all voxel spacings from the API.
    
    Returns:
        pd.DataFrame: DataFrame containing all tomogram voxel spacings and their attributes.
    """
    logger.info("Fetching tomogram voxel spacings data...")
    try:
        voxel_spacings = list(TomogramVoxelSpacing.find(client))
        
        # Convert to DataFrame
        df = pd.DataFrame([vs.to_dict() for vs in voxel_spacings])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching tomogram voxel spacings: {e}")
        return pd.DataFrame()


def fetch_depositions_with_filters(query_filters: List) -> pd.DataFrame:
    """Fetch depositions that match specific filters.
    
    Uses the Deposition.find() method with query_filters to retrieve filtered depositions.
    
    Args:
        query_filters: List of filter expressions for the search.
        
    Returns:
        pd.DataFrame: DataFrame containing filtered depositions.
    """
    logger.info(f"Fetching depositions with filters: {query_filters}")
    try:
        depositions = list(Deposition.find(client, query_filters=query_filters))
        
        # Convert to DataFrame
        df = pd.DataFrame([d.to_dict() for d in depositions])
        
        # Convert date strings to datetime objects
        if not df.empty and 'deposition_date' in df.columns:
            df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching depositions with filters: {e}")
        return pd.DataFrame()


def fetch_datasets_with_filters(query_filters: List) -> pd.DataFrame:
    """Fetch datasets that match specific filters.
    
    Uses the Dataset.find() method with query_filters to retrieve filtered datasets.
    
    Args:
        query_filters: List of filter expressions for the search.
        
    Returns:
        pd.DataFrame: DataFrame containing filtered datasets.
    """
    logger.info(f"Fetching datasets with filters: {query_filters}")
    try:
        datasets = list(Dataset.find(client, query_filters=query_filters))
        
        # Convert to DataFrame
        df = pd.DataFrame([d.to_dict() for d in datasets])
        
        # Convert date strings to datetime objects
        if not df.empty:
            if 'release_date' in df.columns:
                df['release_date'] = pd.to_datetime(df['release_date'])
            if 'deposition_date' in df.columns:
                df['deposition_date'] = pd.to_datetime(df['deposition_date'])
        
        return df
    except Exception as e:
        logger.error(f"Error fetching datasets with filters: {e}")
        return pd.DataFrame()


# Advanced data processing functions for specific analytics

def get_datasets_by_sample_type() -> pd.DataFrame:
    """Get counts of datasets by sample type.
    
    Returns:
        pd.DataFrame: DataFrame with counts of datasets grouped by sample type.
    """
    df = fetch_datasets()
    if df.empty or 'sample_type' not in df.columns:
        return pd.DataFrame(columns=['sample_type', 'count'])
    return df.groupby('sample_type').size().reset_index(name='count').sort_values('count', ascending=False)


def get_datasets_by_organism() -> pd.DataFrame:
    """Get counts of datasets by organism name.
    
    Returns:
        pd.DataFrame: DataFrame with counts of datasets grouped by organism.
    """
    df = fetch_datasets()
    if df.empty or 'organism_name' not in df.columns:
        return pd.DataFrame(columns=['organism_name', 'count'])
    return df.groupby('organism_name').size().reset_index(name='count').sort_values('count', ascending=False)


def get_runs_by_sample_type() -> pd.DataFrame:
    """Get counts of runs by sample type.
    
    Returns:
        pd.DataFrame: DataFrame with counts of runs grouped by sample type.
    """
    df = fetch_runs_with_dataset_dates()
    if df.empty or 'sample_type' not in df.columns:
        return pd.DataFrame(columns=['sample_type', 'count'])
    return df.groupby('sample_type').size().reset_index(name='count').sort_values('count', ascending=False)


def get_runs_by_organism() -> pd.DataFrame:
    """Get counts of runs by organism name.
    
    Returns:
        pd.DataFrame: DataFrame with counts of runs grouped by organism.
    """
    df = fetch_runs_with_dataset_dates()
    if df.empty or 'organism_name' not in df.columns:
        return pd.DataFrame(columns=['organism_name', 'count'])
    return df.groupby('organism_name').size().reset_index(name='count').sort_values('count', ascending=False)


def get_runs_with_annotations() -> pd.DataFrame:
    """Get count of runs with at least one annotation.
    
    Returns:
        pd.DataFrame: DataFrame of runs with a flag indicating if they have annotations.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_data = cache.get("preloaded_runs_with_annotations")
        if preloaded_data is not None:
            logger.info("Using preloaded runs with annotations data from cache")
            return preloaded_data
    except ImportError:
        # Cache might not be initialized yet, continue with normal processing
        pass
        
    runs_df = fetch_runs_with_dataset_dates()
    annotations_df = fetch_annotations()
    
    if runs_df.empty or annotations_df.empty or 'run_id' not in annotations_df.columns:
        # Create empty result with necessary columns
        empty_df = runs_df.copy() if not runs_df.empty else pd.DataFrame()
        empty_df['annotation_count'] = 0
        empty_df['has_annotations'] = False
        return empty_df
    
    # Count annotations per run
    annotations_per_run = annotations_df.groupby('run_id').size().reset_index(name='annotation_count')
    
    # Merge with runs
    runs_with_annotations = runs_df.merge(
        annotations_per_run, 
        left_on='id', 
        right_on='run_id', 
        how='left'
    )
    
    # Fill NaN values with 0
    runs_with_annotations['annotation_count'] = runs_with_annotations['annotation_count'].fillna(0)
    
    # Mark runs with at least one annotation
    runs_with_annotations['has_annotations'] = runs_with_annotations['annotation_count'] > 0
    
    return runs_with_annotations


def get_tomograms_by_reconstruction_method() -> pd.DataFrame:
    """Get counts of tomograms by reconstruction method.
    
    Returns:
        pd.DataFrame: DataFrame with counts of tomograms grouped by reconstruction method.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_data = cache.get("preloaded_tomograms_recon_methods")
        if preloaded_data is not None:
            logger.info("Using preloaded tomogram reconstruction methods data from cache")
            return preloaded_data
    except ImportError:
        # Cache might not be initialized yet, continue with normal processing
        pass
        
    df = fetch_tomograms()
    if df.empty or 'reconstruction_method' not in df.columns:
        return pd.DataFrame(columns=['reconstruction_method', 'count'])
    return df.groupby('reconstruction_method').size().reset_index(name='count').sort_values('count', ascending=False)


def get_tomograms_by_processing_method() -> pd.DataFrame:
    """Get counts of tomograms by processing method.
    
    Returns:
        pd.DataFrame: DataFrame with counts of tomograms grouped by processing method.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_data = cache.get("preloaded_tomograms_proc_methods")
        if preloaded_data is not None:
            logger.info("Using preloaded tomogram processing methods data from cache")
            return preloaded_data
    except ImportError:
        # Cache might not be initialized yet, continue with normal processing
        pass
        
    df = fetch_tomograms()
    if df.empty or 'processing_method' not in df.columns:
        return pd.DataFrame(columns=['processing_method', 'count'])
    return df.groupby('processing_method').size().reset_index(name='count').sort_values('count', ascending=False)


def get_tomograms_by_voxel_spacing() -> pd.DataFrame:
    """Get tomograms by voxel spacing.
    
    Returns:
        pd.DataFrame: DataFrame with counts of tomograms grouped by voxel spacing.
    """
    # Try to get preloaded data from cache first
    try:
        preloaded_data = cache.get("preloaded_tomograms_voxel_spacings")
        if preloaded_data is not None:
            logger.info("Using preloaded tomogram voxel spacings data from cache")
            return preloaded_data
    except ImportError:
        # Cache might not be initialized yet, continue with normal processing
        pass
        
    df = fetch_tomograms()
    if df.empty or 'voxel_spacing' not in df.columns:
        voxel_spacings_df = fetch_tomogram_voxel_spacings()
        if not voxel_spacings_df.empty and 'voxel_spacing' in voxel_spacings_df.columns:
            # Process voxel spacings directly from the dedicated table
            voxel_spacings_df['voxel_spacing'] = pd.to_numeric(voxel_spacings_df['voxel_spacing'], errors='coerce')
            voxel_spacings_df['voxel_spacing_rounded'] = (voxel_spacings_df['voxel_spacing'] * 10).round() / 10
            return voxel_spacings_df.groupby('voxel_spacing_rounded').size().reset_index(name='count').sort_values('voxel_spacing_rounded')
        return pd.DataFrame(columns=['voxel_spacing_rounded', 'count'])
        
    # Convert to numeric
    df['voxel_spacing'] = pd.to_numeric(df['voxel_spacing'], errors='coerce')
    # Group by voxel spacing rounded to nearest 0.1
    df['voxel_spacing_rounded'] = (df['voxel_spacing'] * 10).round() / 10
    return df.groupby('voxel_spacing_rounded').size().reset_index(name='count').sort_values('voxel_spacing_rounded')


def get_annotations_by_method() -> pd.DataFrame:
    """Get counts of annotations by method type.
    
    Categorizes annotations by the method_type field (an enumeration with values
    like 'manual', 'automated', 'hybrid', 'simulated').
    
    Returns:
        pd.DataFrame: DataFrame with counts of annotations grouped by method type.
    """
    df = fetch_annotations()
    
    if df.empty or 'method_type' not in df.columns:
        # Create empty result with expected columns
        return pd.DataFrame(columns=['method_type', 'count'])
    
    # Group by method_type and count
    result = df.groupby('method_type').size().reset_index(name='count').sort_values('count', ascending=False)
    
    # Make method_type more readable by capitalizing first letter
    result['method_type'] = result['method_type'].str.capitalize()
    
    return result


def get_annotations_by_shape() -> pd.DataFrame:
    """Get counts of annotations by shape type.
    
    Queries the AnnotationShape entities and categorizes them by shape_type
    based on the GraphQL schema. Each annotation can have multiple shapes,
    and each shape has a shape_type (SegmentationMask, OrientedPoint, Point, 
    InstanceSegmentation, Mesh).
    
    Returns:
        pd.DataFrame: DataFrame with counts of annotation shapes grouped by shape type.
    """
    logger.info("Getting annotation shapes by type...")
    try:
        # Query AnnotationShape entities directly
        from cryoet_data_portal import AnnotationShape
        
        # Get all shapes
        shapes = list(AnnotationShape.find(client))
        if not shapes:
            logger.warning("No annotation shapes found")
            return pd.DataFrame(columns=['shape_type', 'count'])
            
        # Convert to DataFrame
        shapes_df = pd.DataFrame([s.to_dict() for s in shapes])
        
        if shapes_df.empty or 'shape_type' not in shapes_df.columns:
            logger.warning("No shape_type column in the returned data")
            return pd.DataFrame(columns=['shape_type', 'count'])
            
        # Count by shape_type
        result = shapes_df.groupby('shape_type').size().reset_index(name='count')
        result.sort_values('count', ascending=False, inplace=True)
        
        # Make shape_type more readable by capitalizing first letter and replacing underscores with spaces
        result['shape_type'] = result['shape_type'].str.capitalize().str.replace('_', ' ')
        
        return result
    except Exception as e:
        logger.error(f"Error getting annotation shapes by type: {e}")
        return pd.DataFrame(columns=['shape_type', 'count'])


def get_annotations_by_object() -> pd.DataFrame:
    """Get counts of annotations by annotated object name.
    
    Categorizes annotations by the object_name field.
    
    Returns:
        pd.DataFrame: DataFrame with counts of annotations grouped by object name.
            Includes a URL column for linking to Gene Ontology or UniProtKB.
    """
    df = fetch_annotations()
    
    if df.empty or 'object_name' not in df.columns or 'object_id' not in df.columns:
        # Create empty result with expected columns
        return pd.DataFrame(columns=['object_name', 'count', 'url'])
    
    # Group by object_name and count
    result = df.groupby(['object_name', 'object_id']).size().reset_index(name='count').sort_values('count', ascending=False)
    
    # Create URL based on object_id prefix
    def create_url(row):
        object_id = row['object_id'] if pd.notna(row['object_id']) else ""
        if object_id.startswith('GO:'):
            return f"https://amigo.geneontology.org/amigo/term/{object_id}"
        elif pd.notna(object_id) and len(object_id) > 0:
            # Assume UniProtKB for any other ID
            return f"https://www.uniprot.org/uniprotkb/{object_id}/entry"
        return ""
    
    result['url'] = result.apply(create_url, axis=1)
    
    return result


def fetch_runs_with_dataset_dates() -> pd.DataFrame:
    """Fetch all runs with dataset dates.
    
    Since runs don't have direct date associations, this function fetches runs
    and merges them with their parent datasets to get the dates, sample type,
    and organism information.
    
    Returns:
        pd.DataFrame: DataFrame containing all runs with dataset information.
    """
    logger.info("Fetching runs with dataset information...")
    try:
        # Get all runs
        runs = list(Run.find(client))
        runs_df = pd.DataFrame([r.to_dict() for r in runs])
        
        # Get all datasets
        datasets = list(Dataset.find(client))
        datasets_df = pd.DataFrame([d.to_dict() for d in datasets])
        
        # Convert date strings to datetime objects
        if 'release_date' in datasets_df.columns:
            datasets_df['release_date'] = pd.to_datetime(datasets_df['release_date'])
        if 'deposition_date' in datasets_df.columns:
            datasets_df['deposition_date'] = pd.to_datetime(datasets_df['deposition_date'])
        
        # Get necessary columns from datasets
        # Include dates as well as sample_type and organism_name
        needed_columns = ['id', 'deposition_date', 'release_date', 'sample_type', 'organism_name']
        datasets_info_df = datasets_df[
            [col for col in needed_columns if col in datasets_df.columns]
        ].copy()
        datasets_info_df.rename(columns={'id': 'dataset_id'}, inplace=True)
        
        # Merge runs with datasets to get dates and other metadata
        merged_df = runs_df.merge(
            datasets_info_df, 
            left_on='dataset_id', 
            right_on='dataset_id', 
            how='left'
        )
        
        return merged_df
    except Exception as e:
        logger.error(f"Error fetching runs with dataset information: {e}")
        return pd.DataFrame()


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def get_deposition_images(cache_buster: Optional[int] = None) -> list:
    """
    Get image URLs and captions for depositions.
    
    Args:
        cache_buster: Optional int to bust the cache when refreshing images
    
    Returns:
        List of dictionaries with 'url', 'caption', and 'link' keys
    """
    logger.info("Fetching deposition images...")
    try:
        df = fetch_depositions()
        if 'key_photo_url' not in df.columns or df.empty:
            return []
        
        # Filter out rows without images
        df = df[df['key_photo_url'].notna()]
        
        # Create list of image data
        image_data = []
        for _, row in df.iterrows():
            if row.get('key_photo_url'):
                image_data.append({
                    'url': row['key_photo_url'],
                    'caption': f"Deposition {row['id']}: {row.get('title', '')[:30]}",
                    'link': f"{PORTAL_BASE_URL}/depositions/{row['id']}"
                })
        
        # Randomize the order
        random.shuffle(image_data)
        logger.info(f"Number of deposition images: {len(image_data)}")
        return image_data
    except Exception as e:
        logger.error(f"Error fetching deposition images: {e}")
        return []


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def get_dataset_images(cache_buster: Optional[int] = None) -> list:
    """
    Get image URLs and captions for datasets.
    
    Args:
        cache_buster: Optional int to bust the cache when refreshing images
    
    Returns:
        List of dictionaries with 'url', 'caption', and 'link' keys
    """
    logger.info("Fetching dataset images...")
    try:
        df = fetch_datasets()
        if 'key_photo_url' not in df.columns or df.empty:
            return []
        
        # Filter out rows without images
        df = df[df['key_photo_url'].notna()]
        
        # Create list of image data
        image_data = []
        for _, row in df.iterrows():
            if row.get('key_photo_url'):
                image_data.append({
                    'url': row['key_photo_url'],
                    'caption': f"Dataset {row['id']}: {row.get('title', '')[:30]}",
                    'link': f"{PORTAL_BASE_URL}/datasets/{row['id']}"
                })
        
        # Randomize the order
        random.shuffle(image_data)
        
        return image_data
    except Exception as e:
        logger.error(f"Error fetching dataset images: {e}")
        return []


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def get_run_images(cache_buster: Optional[int] = None) -> list:
    """
    Get image URLs and captions for runs using their first tomogram's key photo.
    
    Args:
        cache_buster: Optional int to bust the cache when refreshing images
    
    Returns:
        List of dictionaries with 'url', 'caption', and 'link' keys
    """
    logger.info("Fetching run images...")
    try:
        # Get runs and tomograms
        runs_df = fetch_runs()
        tomograms_df = fetch_tomograms()
        
        if runs_df.empty or tomograms_df.empty:
            return []
        
        # Ensure we have the necessary columns
        if 'key_photo_url' not in tomograms_df.columns or 'run_id' not in tomograms_df.columns:
            return []
        
        # Filter out rows without images
        tomograms_df = tomograms_df[tomograms_df['key_photo_url'].notna()]
        logger.info(f"Number of tomograms with images: {len(tomograms_df)}")
        
        # Get the first tomogram for each run
        first_tomograms = tomograms_df.sort_values('id').groupby('run_id').first().reset_index()
        logger.info(f"Number of first tomograms: {len(first_tomograms)}")
        
        # Merge with runs to get run information
        merged_df = runs_df.merge(
            first_tomograms[['run_id', 'key_photo_url', 'id']],
            left_on='id',
            right_on='run_id',
            how='inner'
        )
        logger.info(f"Number of merged runs: {len(merged_df)}")
        
        # Create list of image data
        image_data = []
        for _, row in merged_df.iterrows():
            if row.get('key_photo_url'):
                caption = f"Run {row['id_x']}"  # Use id_x as it's from the runs table
                if 'title' in row and row['title']:
                    caption += f": {row['title'][:30]}"
                
                image_data.append({
                    'url': row['key_photo_url'],
                    'caption': caption,
                    'link': f"{PORTAL_BASE_URL}/runs/{row['id_x']}"
                })
        
        logger.info(f"Number of image data before shuffle: {len(image_data)}")
        # Randomize the order
        random.shuffle(image_data)
        
        # Limit to 100 images
        limited_data = image_data[:100]
        logger.info(f"Number of images after limiting: {len(limited_data)}")
        return limited_data
    except Exception as e:
        logger.error(f"Error fetching run images: {e}")
        return []


@cache.memoize(timeout=1800)  # Cache for 30 minutes
def get_tomogram_images(cache_buster: Optional[int] = None) -> list:
    """
    Get image URLs and captions for tomograms.
    
    Args:
        cache_buster: Optional int to bust the cache when refreshing images
    
    Returns:
        List of dictionaries with 'url', 'caption', and 'link' keys
    """
    logger.info("Fetching tomogram images...")
    try:
        df = fetch_tomograms()
        if df.empty:
            return []
        
        # Check if key_photo_url column exists
        if 'key_photo_url' not in df.columns:
            return []
        
        # Filter out rows without images
        df = df[df['key_photo_url'].notna()]
        logger.info(f"Number of tomograms with images: {len(df)}")
        
        # Create list of image data
        image_data = []
        for _, row in df.iterrows():
            if row.get('key_photo_url'):
                caption = f"Tomogram {row['id']}"
                
                # Use the run_id for the link instead of the tomogram id
                if 'run_id' in row and row['run_id']:
                    link = f"{PORTAL_BASE_URL}/runs/{row['run_id']}"
                else:
                    # Fallback to deposition page if run_id is not available
                    link = f"{PORTAL_BASE_URL}/depositions/{row['deposition_id']}"
                
                image_data.append({
                    'url': row['key_photo_url'],
                    'caption': caption,
                    'link': link
                })
        
        logger.info(f"Number of image data before shuffle: {len(image_data)}")
        # Randomize the order
        random.shuffle(image_data)
        
        # Limit to 50 images (will become 100 after duplication in gallery)
        limited_data = image_data[:50]
        logger.info(f"Number of images after limiting: {len(limited_data)}")
        return limited_data
    except Exception as e:
        logger.error(f"Error fetching tomogram images: {e}")
        return []


def get_depositions_for_filtering():
    """Fetch depositions with properly formatted date columns for filtering.
    
    Returns:
        pd.DataFrame: DataFrame with depositions data and properly formatted date columns
    """
    # Get raw depositions data
    depositions_df = fetch_depositions()
    
    # Ensure the deposition_date column is a datetime type
    # Convert to naive datetime to avoid timezone issues
    depositions_df['deposition_date'] = pd.to_datetime(depositions_df['deposition_date']).dt.tz_localize(None)
    
    # Add helper columns for filtering
    depositions_df['year_month'] = depositions_df['deposition_date'].dt.strftime('%Y-%m')
    depositions_df['year'] = depositions_df['deposition_date'].dt.year
    depositions_df['month'] = depositions_df['deposition_date'].dt.month
    
    return depositions_df


def get_datasets_for_filtering():
    """Fetch datasets with properly formatted date columns for filtering.
    
    Returns:
        pd.DataFrame: DataFrame with datasets data and properly formatted date columns
    """
    # Get raw datasets data
    datasets_df = fetch_datasets()
    
    # Ensure the deposition_date column is a datetime type
    # Convert to naive datetime to avoid timezone issues
    datasets_df['deposition_date'] = pd.to_datetime(datasets_df['deposition_date']).dt.tz_localize(None)
    
    # Add helper columns for filtering
    datasets_df['year_month'] = datasets_df['deposition_date'].dt.strftime('%Y-%m')
    datasets_df['year'] = datasets_df['deposition_date'].dt.year
    datasets_df['month'] = datasets_df['deposition_date'].dt.month
    
    return datasets_df


def get_example_annotation_shapes(limit: int = 5) -> pd.DataFrame:
    """Get example annotation shapes for each shape type.
    
    Retrieves annotation shapes and their associated files and annotation metadata
    to provide examples of each shape type.
    
    Args:
        limit: Maximum number of examples to retrieve per shape type
        
    Returns:
        pd.DataFrame: DataFrame containing example annotation shapes with metadata
    """
    logger.info("Getting example annotation shapes...")
    try:
        from cryoet_data_portal import AnnotationShape, Annotation, AnnotationFile
        
        # Get all shapes
        shapes = list(AnnotationShape.find(client))
        if not shapes:
            logger.warning("No annotation shapes found")
            return pd.DataFrame()
            
        # Convert shapes to DataFrame
        shapes_df = pd.DataFrame([s.to_dict() for s in shapes])
        
        if shapes_df.empty:
            return pd.DataFrame()
            
        # Get examples of each shape type (limited number per type)
        examples = []
        for shape_type, group in shapes_df.groupby('shape_type'):
            # Take up to 'limit' examples for each shape type
            examples_of_type = group.head(limit)
            examples.append(examples_of_type)
            
        examples_df = pd.concat(examples) if examples else pd.DataFrame()
        
        if examples_df.empty:
            return pd.DataFrame()
            
        # Get annotations for the examples
        annotation_ids = examples_df['annotation_id'].dropna().unique().tolist()
        annotations = list(Annotation.find(client, where={"id": {"_in": annotation_ids}}))
        annotations_df = pd.DataFrame([a.to_dict() for a in annotations])
        
        # Get annotation files for the shape examples
        shape_ids = examples_df['id'].dropna().unique().tolist()
        annotation_files = list(AnnotationFile.find(client, where={"annotation_shape_id": {"_in": shape_ids}}))
        annotation_files_df = pd.DataFrame([f.to_dict() for f in annotation_files]) if annotation_files else pd.DataFrame()
        
        # Merge shape examples with annotation data
        result_df = examples_df.copy()
        
        if not annotations_df.empty:
            result_df = result_df.merge(
                annotations_df,
                left_on='annotation_id',
                right_on='id',
                how='left',
                suffixes=('_shape', '_annotation')
            )
        
        # Add file information to each shape
        if not annotation_files_df.empty:
            # Group files by shape_id
            files_by_shape = {}
            for shape_id, files in annotation_files_df.groupby('annotation_shape_id'):
                files_by_shape[shape_id] = files.to_dict('records')
            
            # Add a files column to the result dataframe
            result_df['files'] = result_df['id'].map(lambda x: files_by_shape.get(x, []))
            result_df['file_count'] = result_df['files'].apply(len)
            
            # Get representative file URL for each shape (for potential visualization)
            def get_file_url(files):
                if not files:
                    return ""
                # Prefer visualization_default files if available
                viz_files = [f for f in files if f.get('is_visualization_default')]
                if viz_files:
                    return viz_files[0].get('https_path', "")
                return files[0].get('https_path', "")
            
            result_df['representative_file_url'] = result_df['files'].apply(get_file_url)
        
        # Clean up shape type display
        if 'shape_type' in result_df:
            result_df['shape_type_display'] = result_df['shape_type'].str.capitalize().str.replace('_', ' ')
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error getting example annotation shapes: {e}")
        return pd.DataFrame() 