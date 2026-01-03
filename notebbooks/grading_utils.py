"""
Common utilities for AI Handwrite Grader notebooks.
Consolidates repeated code across all notebook steps.
"""

import os
import json
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


# =======================
# Path and Config Setup
# =======================

def setup_paths(prefix: str, data_dir: str, base_dir: str = ".."):
    """
    Generate all standard paths for a grading session.

    Args:
        prefix: Test name prefix (e.g., "VTC Test")
        data_dir: Data files directory name
        base_dir: Base directory relative to notebook (default: "..")

    Returns:
        dict: Dictionary containing all standard paths
    """
    paths = {
        "pdf_file": f"{base_dir}/{data_dir}/{prefix}.pdf",
        "name_list_file": f"{base_dir}/{data_dir}/{prefix} Name List.xlsx",
        "marking_scheme_file": f"{base_dir}/{data_dir}/{prefix} Marking Scheme.xlsx",
    }

    file_name = os.path.splitext(os.path.basename(paths["pdf_file"]))[0]
    base_path = f"{base_dir}/marking_form/{file_name}"

    paths.update({
        "file_name": file_name,
        "base_path": base_path,
        "base_path_images": f"{base_path}/images/",
        "base_path_annotations": f"{base_path}/annotations/",
        "base_path_questions": f"{base_path}/questions",
        "base_path_javascript": f"{base_path}/javascript",
        "base_path_marked_images": f"{base_path}/marked/images/",
        "base_path_marked_pdfs": f"{base_path}/marked/pdf/",
        "base_path_marked_scripts": f"{base_path}/marked/scripts/",
        "cache_dir": f"{base_dir}/cache",
    })

    return paths


def create_directories(paths: dict):
    """Create all necessary directories from paths dictionary."""
    dir_keys = [
        "base_path_images", "base_path_annotations", "base_path_questions",
        "base_path_javascript", "base_path_marked_images",
        "base_path_marked_pdfs", "base_path_marked_scripts", "cache_dir"
    ]
    for key in dir_keys:
        if key in paths:
            os.makedirs(paths[key], exist_ok=True)


# =======================
# Gemini Client Setup
# =======================

def init_gemini_client(env_path: str = "../.env"):
    """
    Initialize Gemini client with API key from .env file.

    Args:
        env_path: Path to .env file

    Returns:
        genai.Client: Initialized Gemini client

    Raises:
        ValueError: If API key is missing or invalid
    """
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")

    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            f"Please set GOOGLE_GENAI_API_KEY in {env_path}\n"
            "Get your API key from: https://aistudio.google.com/apikey"
        )

    client = genai.Client(vertexai=True, api_key=api_key)
    print("✓ Vertex AI Express Mode initialized")
    return client


# =======================
# Caching Functions
# =======================

def get_cache_key(cache_type: str, **params) -> str:
    """
    Generate a cache key from parameters.

    Args:
        cache_type: Type of cached operation
        **params: Additional parameters for cache key

    Returns:
        str: SHA256 hash of the parameters
    """
    key_data = {"type": cache_type, **params}
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()


def get_from_cache(cache_key: str, cache_dir: str = "../cache"):
    """
    Retrieve cached result.

    Args:
        cache_key: Cache key hash
        cache_dir: Cache directory path

    Returns:
        dict or None: Cached data if found
    """
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_to_cache(cache_key: str, data: dict, cache_dir: str = "../cache"):
    """
    Save result to cache.

    Args:
        cache_key: Cache key hash
        data: Data to cache
        cache_dir: Cache directory path
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Warning: Failed to save cache - {e}")


# =======================
# Annotation Loading
# =======================

def load_annotations(annotations_path: str):
    """
    Load and process annotations from JSON file.

    Args:
        annotations_path: Path to annotations.json

    Returns:
        tuple: (annotations_list, annotations_dict, questions)
            - annotations_list: Flattened list of all annotations
            - annotations_dict: Dict keyed by label
            - questions: Sorted list of question labels (excluding NAME, ID, CLASS)
    """
    with open(annotations_path, "r") as f:
        annotations = json.load(f)

    # Flatten annotations to list
    annotations_list = []
    for page in annotations:
        for annotation in annotations[page]:
            annotation["page"] = int(page)
            annotation["left"] = annotation.pop("x")
            annotation["top"] = annotation.pop("y")
            annotations_list.append(annotation)

    # Convert to dict keyed by label
    annotations_dict = {ann["label"]: ann for ann in annotations_list}

    # Extract question labels
    questions = []
    for ann in annotations_list:
        label = ann["label"]
        if label not in questions:
            questions.append(label)

    # Remove metadata labels and sort
    for meta_label in ["NAME", "ID", "CLASS"]:
        if meta_label in questions:
            questions.remove(meta_label)

    questions.sort()
    questions = ["NAME", "ID", "CLASS"] + questions

    return annotations_list, annotations_dict, questions


# =======================
# Student ID Mapping
# =======================

def build_student_id_mapping(base_path_questions: str, base_path_annotations: str):
    """
    Build mapping between pages and student IDs.

    Args:
        base_path_questions: Path to questions directory
        base_path_annotations: Path to annotations directory

    Returns:
        tuple: (pageToStudentId dict, numberOfPages, getStudentId function)
    """
    # Get number of pages from annotations
    with open(os.path.join(base_path_annotations, "annotations.json")) as f:
        data = json.load(f)
        numberOfPage = len(data)

    # Build page to student ID mapping
    pageToStudentId = {}
    id_mark_path = os.path.join(base_path_questions, "ID", "mark.json")
    with open(id_mark_path) as f:
        data = json.load(f)
        for item in data:
            pageToStudentId[item["id"]] = (
                item["overridedMark"] if item["overridedMark"] != "" else item["mark"]
            )

    def getStudentId(page: int) -> str:
        """Get student ID for a given page by searching backwards."""
        for p in range(page, page - numberOfPage, -1):
            if str(p) in pageToStudentId:
                return pageToStudentId[str(p)]
        print(f"Warning: {page} is not in pageToStudentId!")
        return None

    return pageToStudentId, numberOfPage, getStudentId


# =======================
# Gemini Config Helpers
# =======================

def get_default_safety_settings():
    """Get default safety settings for Gemini API."""
    return [
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_ONLY_HIGH"),
    ]


def create_gemini_config(temperature=0, top_p=0.5, max_output_tokens=4096, **kwargs):
    """
    Create a standard Gemini generation config.

    Args:
        temperature: Sampling temperature (0-1)
        top_p: Top-p sampling parameter
        max_output_tokens: Maximum output tokens
        **kwargs: Additional config parameters

    Returns:
        types.GenerateContentConfig
    """
    config_params = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_output_tokens,
        "safety_settings": get_default_safety_settings(),
    }
    config_params.update(kwargs)
    return types.GenerateContentConfig(**config_params)


# =======================
# Markdown Conversion
# =======================

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to HTML without external libraries.

    Args:
        markdown_text: Markdown formatted text

    Returns:
        str: HTML formatted text
    """
    import re

    if not markdown_text:
        return ""

    html = str(markdown_text)

    # Convert headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Convert bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)

    # Convert bullet points
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if re.match(r'^[\*\-\+]\s+', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = re.sub(r'^[\*\-\+]\s+', '', line)
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')

    html = '\n'.join(result)

    # Convert paragraphs
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = f'<p>{html}</p>'

    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<p>\s*<(h[1-6]|ul)>', r'<\1>', html)
    html = re.sub(r'</(h[1-6]|ul)>\s*</p>', r'</\1>', html)

    return html
