"""AI Classification Service for animal breed detection.

This service uses HuggingFace transformers to classify animal images
and detect species (Dog, Cat, Other) and breed.

Models used:
- Species detection: google/vit-base-patch16-224 (ImageNet)
- Dog breed: prithivMLmods/Dog-Breed-120 (120 dog breeds, 86.8% accuracy)
- Cat breed: dima806/cat_breed_image_detection (48 cat breeds, 77% accuracy)
"""
from __future__ import annotations

import base64
import io
import os
import re
import threading
from typing import Optional, Tuple, List, Dict, Any

from models.classification_result import ClassificationResult, BreedPrediction
import app_config


class AIClassificationConfig:
    """Configuration for AI classification feature."""
    
    ENABLED = True
    
    SPECIES_MODEL = "google/vit-base-patch16-224"
    DOG_BREED_MODEL = "prithivMLmods/Dog-Breed-120"
    CAT_BREED_MODEL = "dima806/cat_breed_image_detection"
    
    MIN_SPECIES_CONFIDENCE = 0.60   # Below this → "Not Specified Species"
    MIN_BREED_CONFIDENCE = 0.58     # Below this → Suggest "Mixed Breed" (Aspin/Puspin)
    
    LOW_CONFIDENCE_DOG_LABEL = "Aspin (Mixed Breed)"
    LOW_CONFIDENCE_CAT_LABEL = "Puspin (Mixed Breed)"
    
    MODEL_CACHE_DIR = str(app_config.STORAGE_DIR / "ai_models")
    
    CLASSIFICATION_TIMEOUT = 60
    
    TOP_N_PREDICTIONS = 3
    
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_BASE = 2  # seconds (exponential backoff: 2, 4, 8...)
    
    MODEL_SIZES = {
        "species": 330,  # google/vit-base-patch16-224
        "dog_breed": 340,  # prithivMLmods/Dog-Breed-120
        "cat_breed": 340,  # dima806/cat_breed_image_detection
    }
    
    DOG_KEYWORDS = {
        "dog", "puppy", "hound", "terrier", "retriever", "shepherd", "bulldog",
        "poodle", "beagle", "collie", "spaniel", "husky", "malamute", "corgi",
        "dachshund", "chihuahua", "pug", "boxer", "doberman", "rottweiler",
        "labrador", "golden", "german", "shih", "maltese", "pomeranian",
        "schnauzer", "mastiff", "dane", "setter", "pointer", "weimaraner",
        "vizsla", "basenji", "akita", "samoyed", "chow", "dalmatian",
        "greyhound", "whippet", "borzoi", "afghan", "saluki", "newfoundland",
        "saint bernard", "bernese", "great pyrenees", "leonberger", "kuvasz"
    }
    
    CAT_KEYWORDS = {
        "cat", "kitten", "feline", "tabby", "persian", "siamese", "maine coon",
        "ragdoll", "bengal", "sphynx", "abyssinian", "scottish fold", "british",
        "russian blue", "norwegian", "birman", "burmese", "oriental", "himalayan",
        "egyptian mau", "tonkinese", "turkish", "manx", "somali", "balinese"
    }


class AIClassificationService:
    """Service for classifying animal images using AI models.
    
    This service provides:
    - Species detection (Dog, Cat, Other)
    - Breed classification for dogs and cats
    - Philippine breed support (Aspin/Puspin for mixed breeds)
    - Lazy model loading (models downloaded on first use)
    - Thread-safe singleton pattern
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for model caching."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the service (lazy loading - models loaded on first use)."""
        if self._initialized:
            return
        
        self._initialized = True
        self._species_model = None
        self._species_processor = None
        self._dog_model = None
        self._dog_processor = None
        self._cat_model = None
        self._cat_processor = None
        self._models_available = None  # None = not checked, True/False = result
        self._cancel_requested = False  # Cancellation flag for downloads
        self._download_lock = threading.Lock()  # Prevent concurrent downloads
        self._is_downloading = False  # Track if download is in progress
        
        # Progress tracking for UI
        self._download_progress = {
            "current_step": 0,
            "total_steps": 3,
            "message": "Waiting to start...",
            "progress": 0.0
        }
        
        os.makedirs(AIClassificationConfig.MODEL_CACHE_DIR, exist_ok=True)
    
    def is_available(self) -> bool:
        """Check if AI classification is available (dependencies installed)."""
        if self._models_available is not None:
            return self._models_available
        
        try:
            import torch
            import transformers
            from PIL import Image
            self._models_available = True
        except ImportError:
            self._models_available = False
        
        return self._models_available
    
    def _load_species_model(self, resume_download: bool = True) -> bool:
        """Load the species detection model with retry logic. Returns True if successful."""
        if self._species_model is not None:
            return True
        
        return self._load_model_with_retry(
            model_name=AIClassificationConfig.SPECIES_MODEL,
            model_type="species",
            resume_download=resume_download
        )
    
    def _load_dog_model(self, resume_download: bool = True) -> bool:
        """Load the dog breed classification model with retry logic. Returns True if successful."""
        if self._dog_model is not None:
            return True
        
        return self._load_model_with_retry(
            model_name=AIClassificationConfig.DOG_BREED_MODEL,
            model_type="dog_breed",
            resume_download=resume_download
        )
    
    def _load_cat_model(self, resume_download: bool = True) -> bool:
        """Load the cat breed classification model with retry logic. Returns True if successful."""
        if self._cat_model is not None:
            return True
        
        return self._load_model_with_retry(
            model_name=AIClassificationConfig.CAT_BREED_MODEL,
            model_type="cat_breed",
            resume_download=resume_download
        )
    
    def _load_model_with_retry(
        self, 
        model_name: str, 
        model_type: str, 
        resume_download: bool = True
    ) -> bool:
        """Load a model with retry logic and resumption support.
        
        Args:
            model_name: HuggingFace model identifier
            model_type: One of 'species', 'dog_breed', 'cat_breed'
            resume_download: Whether to resume partial downloads
            
        Returns:
            True if model loaded successfully
        """
        import time
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        
        for attempt in range(AIClassificationConfig.MAX_RETRY_ATTEMPTS):
            if self._cancel_requested:
                print(f"[AI] Download cancelled for {model_type}")
                return False
            
            try:
                if attempt > 0:
                    delay = AIClassificationConfig.RETRY_DELAY_BASE ** attempt
                    print(f"[AI] Retry attempt {attempt + 1}/{AIClassificationConfig.MAX_RETRY_ATTEMPTS} for {model_type} after {delay}s...")
                    for _ in range(int(delay * 2)):
                        if self._cancel_requested:
                            print(f"[AI] Download cancelled during retry delay for {model_type}")
                            return False
                        time.sleep(0.5)
                
                print(f"[AI] Loading {model_type} model: {model_name}")
                
                result = {"processor": None, "model": None, "error": None}
                
                def load_in_thread():
                    try:
                        result["processor"] = AutoImageProcessor.from_pretrained(
                            model_name,
                            cache_dir=AIClassificationConfig.MODEL_CACHE_DIR,
                            use_fast=True,
                            resume_download=resume_download,
                            local_files_only=False,
                        )
                        
                        if self._cancel_requested:
                            return
                        
                        result["model"] = AutoModelForImageClassification.from_pretrained(
                            model_name,
                            cache_dir=AIClassificationConfig.MODEL_CACHE_DIR,
                            resume_download=resume_download,
                            local_files_only=False,
                        )
                        
                        if result["model"] is not None:
                            result["model"].eval()
                    except Exception as e:
                        result["error"] = e
                
                load_thread = threading.Thread(target=load_in_thread, daemon=True)
                load_thread.start()
                
                # Wait for thread with periodic cancellation and network checks
                cancelled_during_load = False
                network_check_counter = 0
                network_was_lost = False
                while load_thread.is_alive():
                    if self._cancel_requested and not cancelled_during_load:
                        print(f"[AI] Download cancelled during model loading for {model_type}")
                        print(f"[AI] Waiting for current file to complete...")
                        cancelled_during_load = True
                        # Don't return yet - wait for HuggingFace download to finish
                    
                    network_check_counter += 1
                    if network_check_counter >= 10:
                        network_check_counter = 0
                        has_network = self._check_network_connectivity()
                        
                        if not has_network and not network_was_lost:
                            print(f"[AI] Warning: Network connection lost during download")
                            network_was_lost = True
                            self._download_progress["message"] = "⚠️ Network connection lost. Waiting for reconnection..."
                            if hasattr(self, '_current_progress_callback') and self._current_progress_callback:
                                self._current_progress_callback(
                                    self._download_progress["current_step"],
                                    self._download_progress["total_steps"],
                                    self._download_progress["message"]
                                )
                        elif has_network and network_was_lost:
                            print(f"[AI] Network connection restored, resuming download")
                            network_was_lost = False
                            self._download_progress["message"] = f"✓ Connection restored. Resuming download..."
                            self._download_progress["network_restored"] = True
                            # Call progress callback to update UI
                            if hasattr(self, '_current_progress_callback') and self._current_progress_callback:
                                self._current_progress_callback(
                                    self._download_progress["current_step"],
                                    self._download_progress["total_steps"],
                                    self._download_progress["message"]
                                )
                            import time
                            time.sleep(2)
                            if not self._cancel_requested:
                                self._download_progress["message"] = f"Loading {model_type} model..."
                                if hasattr(self, '_current_progress_callback') and self._current_progress_callback:
                                    self._current_progress_callback(
                                        self._download_progress["current_step"],
                                        self._download_progress["total_steps"],
                                        self._download_progress["message"]
                                    )
                    
                    load_thread.join(timeout=0.5)
                
                # If we were cancelled, return now that thread is done
                if cancelled_during_load:
                    print(f"[AI] Current file completed, cancellation complete for {model_type}")
                    return False
                
                if result["error"] is not None:
                    raise result["error"]
                
                if self._cancel_requested:
                    print(f"[AI] Download cancelled after loading {model_type}")
                    return False
                
                processor = result["processor"]
                model = result["model"]
                
                if model_type == "species":
                    self._species_processor = processor
                    self._species_model = model
                elif model_type == "dog_breed":
                    self._dog_processor = processor
                    self._dog_model = model
                elif model_type == "cat_breed":
                    self._cat_processor = processor
                    self._cat_model = model
                
                print(f"[AI] {model_type} model loaded successfully")
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
                    print(f"[AI] Network error loading {model_type}: {e}")
                elif "disk" in error_msg or "space" in error_msg:
                    print(f"[AI] Disk space error loading {model_type}: {e}")
                    return False  # Don't retry on disk space issues
                elif "permission" in error_msg:
                    print(f"[AI] Permission error loading {model_type}: {e}")
                    return False  # Don't retry on permission issues
                else:
                    print(f"[AI] Error loading {model_type}: {e}")
                
                # If this was the last attempt, return False
                if attempt == AIClassificationConfig.MAX_RETRY_ATTEMPTS - 1:
                    print(f"[AI] Failed to load {model_type} after {AIClassificationConfig.MAX_RETRY_ATTEMPTS} attempts")
                    return False
        
        return False
    
    def _check_network_connectivity(self) -> bool:
        """Check if network connection is available."""
        try:
            import socket
            # Try to connect to HuggingFace
            socket.create_connection(("huggingface.co", 443), timeout=5)
            return True
        except OSError:
            return False
    
    def _format_breed_name(self, raw_name: str) -> str:
        """Format breed name from model output to human-readable form.
        
        Examples:
            "golden_retriever" -> "Golden Retriever"
            "german_shepherd" -> "German Shepherd"
            "shih-tzu" -> "Shih Tzu"
        """
        if not raw_name:
            return "Not Specified"
        
        # Replace underscores and hyphens with spaces
        formatted = raw_name.replace("_", " ").replace("-", " ")
        
        formatted = " ".join(word.capitalize() for word in formatted.split())
        
        special_cases = {
            "Shih Tzu": "Shih Tzu",
            "Lhasa": "Lhasa Apso",
            "Pembroke": "Pembroke Welsh Corgi",
            "Cardigan": "Cardigan Welsh Corgi",
            "Boston Bull": "Boston Terrier",
            "Toy Poodle": "Toy Poodle",
            "Miniature Poodle": "Miniature Poodle",
            "Standard Poodle": "Standard Poodle",
        }
        
        for key, value in special_cases.items():
            if key.lower() in formatted.lower():
                return value
        
        return formatted
    
    def _detect_species_from_imagenet(self, image) -> Tuple[str, float]:
        """Detect species using ImageNet model predictions.
        
        Returns:
            Tuple of (species, confidence) where species is "Dog", "Cat", or "Other"
        """
        import torch
        
        if not self._load_species_model():
            return "Other", 0.0
        
        try:
            inputs = self._species_processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self._species_model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=1).squeeze()
            
            top_probs, top_indices = torch.topk(probs, k=10)
            
            dog_score = 0.0
            cat_score = 0.0
            
            id2label = self._species_model.config.id2label
            
            for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
                label = id2label[idx].lower()
                
                for keyword in AIClassificationConfig.DOG_KEYWORDS:
                    if keyword in label:
                        dog_score += prob
                        break
                
                for keyword in AIClassificationConfig.CAT_KEYWORDS:
                    if keyword in label:
                        cat_score += prob
                        break
            
            # Determine species
            if dog_score > cat_score and dog_score > AIClassificationConfig.MIN_SPECIES_CONFIDENCE:
                return "Dog", min(dog_score, 1.0)
            elif cat_score > dog_score and cat_score > AIClassificationConfig.MIN_SPECIES_CONFIDENCE:
                return "Cat", min(cat_score, 1.0)
            elif dog_score > 0.3 or cat_score > 0.3:
                if dog_score >= cat_score:
                    return "Dog", dog_score
                else:
                    return "Cat", cat_score
            else:
                return "Other", max(1.0 - dog_score - cat_score, 0.0)
                
        except Exception as e:
            print(f"[AI] Species detection error: {e}")
            return "Other", 0.0
    
    def _classify_dog_breed(self, image) -> Tuple[str, float, List[BreedPrediction]]:
        """Classify dog breed.
        
        Returns:
            Tuple of (breed_name, confidence, alternative_breeds)
        """
        import torch
        
        if not self._load_dog_model():
            return "Not Specified", 0.0, []
        
        try:
            inputs = self._dog_processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self._dog_model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=1).squeeze()
            
            top_probs, top_indices = torch.topk(probs, k=AIClassificationConfig.TOP_N_PREDICTIONS + 1)
            
            id2label = self._dog_model.config.id2label
            
            top_idx = top_indices[0].item()
            top_prob = top_probs[0].item()
            raw_breed = id2label[top_idx]
            formatted_breed = self._format_breed_name(raw_breed)
            
            alternatives = []
            for i in range(1, len(top_indices)):
                idx = top_indices[i].item()
                prob = top_probs[i].item()
                alt_breed = self._format_breed_name(id2label[idx])
                alternatives.append(BreedPrediction(breed=alt_breed, confidence=prob))
            
            return formatted_breed, top_prob, alternatives
            
        except Exception as e:
            print(f"[AI] Dog breed classification error: {e}")
            return "Not Specified", 0.0, []
    
    def _classify_cat_breed(self, image) -> Tuple[str, float, List[BreedPrediction]]:
        """Classify cat breed.
        
        Returns:
            Tuple of (breed_name, confidence, alternative_breeds)
        """
        import torch
        
        if not self._load_cat_model():
            return "Not Specified", 0.0, []
        
        try:
            inputs = self._cat_processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self._cat_model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=1).squeeze()
            
            top_probs, top_indices = torch.topk(probs, k=AIClassificationConfig.TOP_N_PREDICTIONS + 1)
            
            id2label = self._cat_model.config.id2label
            
            top_idx = top_indices[0].item()
            top_prob = top_probs[0].item()
            raw_breed = id2label[top_idx]
            formatted_breed = self._format_breed_name(raw_breed)
            
            alternatives = []
            for i in range(1, len(top_indices)):
                idx = top_indices[i].item()
                prob = top_probs[i].item()
                alt_breed = self._format_breed_name(id2label[idx])
                alternatives.append(BreedPrediction(breed=alt_breed, confidence=prob))
            
            return formatted_breed, top_prob, alternatives
            
        except Exception as e:
            print(f"[AI] Cat breed classification error: {e}")
            return "Not Specified", 0.0, []
    
    def _load_image(self, image_source: str) -> Optional[Any]:
        """Load image from base64 string or file path.
        
        Args:
            image_source: Either a base64-encoded string or a file path
            
        Returns:
            PIL Image object or None if loading failed
        """
        try:
            from PIL import Image
            
            if len(image_source) > 500 or ";" in image_source[:100]:
                # Likely base64
                if "base64," in image_source:
                    image_source = image_source.split("base64,")[1]
                
                image_bytes = base64.b64decode(image_source)
                image = Image.open(io.BytesIO(image_bytes))
            else:
                if os.path.exists(image_source):
                    image = Image.open(image_source)
                else:
                    upload_path = app_config.UPLOADS_DIR / image_source
                    if upload_path.exists():
                        image = Image.open(upload_path)
                    else:
                        return None
            
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            return image
            
        except Exception as e:
            print(f"[AI] Failed to load image: {e}")
            return None
    
    def classify_image(self, image_source: str, progress_callback=None) -> ClassificationResult:
        """Classify an animal image to detect species and breed.
        
        Args:
            image_source: Either a base64-encoded image string or file path
            progress_callback: Optional callback function(step, total, message) for download progress
            
        Returns:
            ClassificationResult with species, breed, and confidence scores
        """
        if not self.is_available():
            return ClassificationResult.from_error(
                "AI classification is not available. Please install: pip install transformers torch torchvision"
            )
        
        if not all(self.get_download_status().values()):
            if progress_callback:
                success = self.download_all_models(progress_callback=progress_callback)
                if not success:
                    return ClassificationResult.from_error("Failed to download AI models")
        
        image = self._load_image(image_source)
        if image is None:
            return ClassificationResult.from_error("Failed to load image. Please try a different image.")
        
        try:
            # Step 1: Detect species
            species, species_confidence = self._detect_species_from_imagenet(image)
            
            if species == "Other":
                return ClassificationResult(
                    species="Other",
                    species_confidence=species_confidence,
                    breed="Not Applicable",
                    breed_confidence=0.0,
                    is_mixed_breed=False,
                )
            
            # Step 2: Classify breed based on species
            if species == "Dog":
                breed, breed_confidence, alternatives = self._classify_dog_breed(image)
                mixed_label = AIClassificationConfig.LOW_CONFIDENCE_DOG_LABEL
            else:  # Cat
                breed, breed_confidence, alternatives = self._classify_cat_breed(image)
                mixed_label = AIClassificationConfig.LOW_CONFIDENCE_CAT_LABEL
            
            # Step 3: Check if breed confidence is too low (suggest mixed breed)
            is_mixed = breed_confidence < AIClassificationConfig.MIN_BREED_CONFIDENCE
            
            if is_mixed:
                if breed != "Not Specified":
                    alternatives.insert(0, BreedPrediction(breed=breed, confidence=breed_confidence))
                breed = mixed_label
            
            return ClassificationResult(
                species=species,
                species_confidence=species_confidence,
                breed=breed,
                breed_confidence=breed_confidence if not is_mixed else 0.0,
                alternative_breeds=alternatives[:AIClassificationConfig.TOP_N_PREDICTIONS],
                is_mixed_breed=is_mixed,
                raw_breed=breed if not is_mixed else "",
            )
            
        except Exception as e:
            print(f"[AI] Classification error: {e}")
            import traceback
            traceback.print_exc()
            return ClassificationResult.from_error(f"Classification failed: {str(e)}")
    
    def get_download_status(self) -> Dict[str, bool]:
        """Check which models are already downloaded by checking cache files.
        
        Returns:
            Dict with model names and their download status
        """
        import pathlib
        
        cache_dir = pathlib.Path(AIClassificationConfig.MODEL_CACHE_DIR)
        
        def model_exists(model_name: str) -> bool:
            """Check if model files exist in cache."""
            # HuggingFace uses models--org--name directory structure
            model_dir_name = f"models--{model_name.replace('/', '--')}"
            model_path = cache_dir / model_dir_name
            
            if not model_path.exists():
                return False
            
            snapshots_dir = model_path / "snapshots"
            if not snapshots_dir.exists():
                return False
            
            for snapshot in snapshots_dir.iterdir():
                if snapshot.is_dir():
                    has_config = (snapshot / "config.json").exists()
                    has_model = (
                        (snapshot / "pytorch_model.bin").exists() or 
                        (snapshot / "model.safetensors").exists()
                    )
                    if has_config and has_model:
                        return True
            
            return False
        
        return {
            "species": model_exists(AIClassificationConfig.SPECIES_MODEL),
            "dog_breed": model_exists(AIClassificationConfig.DOG_BREED_MODEL),
            "cat_breed": model_exists(AIClassificationConfig.CAT_BREED_MODEL),
        }
    
    def cancel_download(self) -> None:
        """Cancel ongoing download operation."""
        self._cancel_requested = True
        print("[AI] Download cancellation requested")
    
    def is_downloading(self) -> bool:
        """Check if a download is currently in progress.
        
        Returns:
            True if download is ongoing
        """
        return self._is_downloading
    
    def get_download_progress(self) -> Dict[str, Any]:
        """Get the current download progress state.
        
        Returns:
            Dict with current_step, total_steps, message, and progress (0.0-1.0)
        """
        return self._download_progress.copy()
    
    def get_total_download_size(self) -> int:
        """Get estimated total download size in MB.
        
        Returns:
            Total size in megabytes
        """
        download_status = self.get_download_status()
        total_size = 0
        
        for model_type, is_downloaded in download_status.items():
            if not is_downloaded:
                total_size += AIClassificationConfig.MODEL_SIZES.get(model_type, 0)
        
        return total_size
    
    def preload_models(self, species: Optional[str] = None) -> bool:
        """Preload models into memory.
        
        Args:
            species: Optional species to preload specific model ("Dog" or "Cat")
                    If None, loads species model only
        
        Returns:
            True if models loaded successfully
        """
        if not self.is_available():
            return False
        
        success = self._load_species_model()
        
        if species == "Dog":
            success = success and self._load_dog_model()
        elif species == "Cat":
            success = success and self._load_cat_model()
        
        return success
    
    def download_all_models(self, progress_callback=None) -> bool:
        """Download all AI models with progress tracking, retry logic, and resumption.
        
        Args:
            progress_callback: Optional callback function(step, total, message) 
                             to report download progress
        
        Returns:
            True if all models downloaded successfully
        """
        if not self._download_lock.acquire(blocking=False):
            print("[AI] Download already in progress, skipping duplicate request")
            if progress_callback:
                progress_callback(0, 3, "Download already in progress...")
            return False
        
        try:
            self._is_downloading = True
            self._cancel_requested = False
            self._current_progress_callback = progress_callback
            
            # Helper to update progress and call callback
            def update_progress(current: int, total: int, message: str):
                self._download_progress = {
                    "current_step": current,
                    "total_steps": total,
                    "message": message,
                    "progress": current / total if total > 0 else 0.0
                }
                if progress_callback:
                    progress_callback(current, total, message)
            
            if not self.is_available():
                update_progress(0, 3, "AI dependencies not available")
                return False
            
            update_progress(0, 3, "Checking network connection...")
            
            if not self._check_network_connectivity():
                error_msg = "No network connection. Please check your internet and try again."
                print(f"[AI] {error_msg}")
                update_progress(0, 3, error_msg)
                return False
            
            download_status = self.get_download_status()
            total_size = self.get_total_download_size()
            
            if total_size > 0:
                update_progress(0, 3, f"Preparing to download ~{total_size}MB of AI models...")
            
            total_steps = 3
            current_step = 0
            
            # Step 1: Download species model
            size_info = f" (~{AIClassificationConfig.MODEL_SIZES['species']}MB)" if not download_status['species'] else " (cached)"
            update_progress(current_step, total_steps, f"Loading species detection model{size_info}...")
            
            success = self._load_species_model(resume_download=True)
            if not success or self._cancel_requested:
                if self._cancel_requested:
                    update_progress(current_step, total_steps, "Download cancelled")
                    return False
                update_progress(current_step, total_steps, "Failed to download species model. Check connection and try again.")
                return False
            
            current_step += 1
            update_progress(current_step, total_steps, "Species model ready ✓")
            
            # Step 2: Download dog breed model
            size_info = f" (~{AIClassificationConfig.MODEL_SIZES['dog_breed']}MB)" if not download_status['dog_breed'] else " (cached)"
            update_progress(current_step, total_steps, f"Loading dog breed model{size_info} (120 breeds)...")
            
            success = self._load_dog_model(resume_download=True)
            if not success or self._cancel_requested:
                if self._cancel_requested:
                    update_progress(current_step, total_steps, "Download cancelled")
                    return False
                update_progress(current_step, total_steps, "Failed to download dog breed model. Check connection and try again.")
                return False
            
            current_step += 1
            update_progress(current_step, total_steps, "Dog breed model ready ✓")
            
            # Step 3: Download cat breed model
            size_info = f" (~{AIClassificationConfig.MODEL_SIZES['cat_breed']}MB)" if not download_status['cat_breed'] else " (cached)"
            update_progress(current_step, total_steps, f"Loading cat breed model{size_info} (48 breeds)...")
            
            success = self._load_cat_model(resume_download=True)
            if not success or self._cancel_requested:
                if self._cancel_requested:
                    update_progress(current_step, total_steps, "Download cancelled")
                    return False
                update_progress(current_step, total_steps, "Failed to download cat breed model. Check connection and try again.")
                return False
            
            current_step += 1
            update_progress(current_step, total_steps, "All models ready! AI classification enabled. ✓")
            
            return True
        
        except Exception as e:
            error_msg = str(e).lower()
            user_message = "Download failed: "
            
            if "connection" in error_msg or "network" in error_msg:
                user_message += "Network error. Check your connection and try again."
            elif "disk" in error_msg or "space" in error_msg:
                user_message += "Insufficient disk space. Free up space and try again."
            elif "permission" in error_msg:
                user_message += "Permission denied. Check folder permissions."
            else:
                user_message += str(e)
            
            print(f"[AI] Model download error: {e}")
            update_progress(current_step, total_steps, user_message)
            return False
        
        finally:
            # Always release the lock and reset download flag
            self._is_downloading = False
            self._download_lock.release()


def get_ai_classification_service() -> AIClassificationService:
    """Get the singleton AI classification service instance."""
    return AIClassificationService()


__all__ = ["AIClassificationService", "AIClassificationConfig", "get_ai_classification_service"]
