"""Module for preloading data in the background when the app starts."""
import threading
import time
import logging
from cryoet_data_portal_dashboard.data_utils import (
    fetch_tomograms,
    fetch_annotations,
    fetch_runs,
    get_tomograms_by_reconstruction_method,
    get_tomograms_by_processing_method,
    get_tomograms_by_voxel_spacing,
    get_runs_with_annotations
)
from cryoet_data_portal_dashboard.cache import cache

# Get a logger for this module
logger = logging.getLogger(__name__)

def preload_data_in_background():
    """Start a background thread to preload data for all pages.
    
    This function starts a daemon thread that loads data for the heavier pages
    (tomograms, annotations, runs) and stores the results in cache.
    """
    thread = threading.Thread(target=_preload_data_worker, daemon=True)
    thread.start()
    logger.info("Background data preloading thread started")
    return thread

def _preload_data_worker():
    """Worker function that fetches data for heavy pages and stores in cache."""
    try:
        logger.info("Starting background data preloading...")
        
        # Wait a short delay to ensure the app has fully initialized
        time.sleep(2)
        
        # Preload tomograms data
        logger.info("Preloading tomograms data...")
        tomograms_df = fetch_tomograms()
        cache.set("preloaded_tomograms", tomograms_df)
        
        # Preload tomogram statistics
        logger.info("Preloading tomogram statistics...")
        recon_methods = get_tomograms_by_reconstruction_method()
        proc_methods = get_tomograms_by_processing_method()
        voxel_spacings = get_tomograms_by_voxel_spacing()
        cache.set("preloaded_tomograms_recon_methods", recon_methods)
        cache.set("preloaded_tomograms_proc_methods", proc_methods)
        cache.set("preloaded_tomograms_voxel_spacings", voxel_spacings)
        
        # Preload annotations data
        logger.info("Preloading annotations data...")
        annotations_df = fetch_annotations()
        cache.set("preloaded_annotations", annotations_df)
        
        # Preload runs data
        logger.info("Preloading runs data...")
        runs_df = fetch_runs()
        cache.set("preloaded_runs", runs_df)
        
        # Preload runs with annotations
        logger.info("Preloading runs with annotations data...")
        runs_with_annotations = get_runs_with_annotations()
        cache.set("preloaded_runs_with_annotations", runs_with_annotations)
        
        logger.info("Background data preloading completed successfully")
    
    except Exception as e:
        logger.error(f"Error in background data preloading: {e}") 