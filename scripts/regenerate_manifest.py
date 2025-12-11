"""  # Module docstring: explains purpose, inputs, outputs, and validations
Regenerate `manifest.json` capturing file paths, sizes, SHA256 checksums, and categories.

Overview
- Walks the repository root to index regular files and categorize them by directory.
- Derives `run_id` from `reports/project_summary.md` when available; otherwise falls back
  to the previous manifest or current UTC timestamp.
- Writes a reproducible, sorted `manifest.json` with metadata for integrity checks.

Usage
    python scripts/regenerate_manifest.py

Outputs
- `manifest.json` at the repo root with fields: `run_id`, `generated_at`, and `files` list.

Notes
- Skips `.git` and the manifest being written to avoid self-inclusion.
- Paths are normalized to forward slashes for portability.
"""
# Import standard libraries used for filesystem traversal, JSON handling,
# hashing, path manipulation, and timestamps.
import os  # Operating system interfaces (e.g., os.walk)
import json  # JSON encoding/decoding
import hashlib  # Hashing algorithms (SHA256)
from pathlib import Path  # Object-oriented filesystem paths
from datetime import datetime  # Date and time objects


def sha256_file(path: Path) -> str:  # Function to compute SHA256 hash of a file
    # Initialize a SHA256 hash object.
    h = hashlib.sha256()
    # Open the file in binary mode and stream its bytes in chunks.
    with path.open('rb') as f:  # Open file in read-binary mode
        for chunk in iter(lambda: f.read(8192), b''):  # Read in 8KB chunks
            # Update the hash with each chunk to avoid loading large files into memory.
            h.update(chunk)  # Update hash with current chunk
    # Return the hexadecimal digest string.
    return h.hexdigest()  # Get hexadecimal representation of hash


def categorize(root: Path, file_path: Path):  # Function to categorize a file based on its path
    # Compute the file's path relative to the repository root.
    rel = file_path.relative_to(root)  # Get relative path
    # Break the relative path into its directory components.
    parts = rel.parts  # Get path components as a tuple
    # If the path has no parts (edge case), fall back to root/misc.
    if not parts:  # Check if path is empty
        return ("root", "misc")  # Default category for empty path

    # The top-level directory determines the primary category.
    top = parts[0]  # Get the first part of the path
    if top == 'data':  # If top-level is 'data'
        # Distinguish between datasets and labels under data/.
        sub = 'labels' if len(parts) > 1 and parts[1] == 'labels' else 'datasets'  # Determine subcategory
        return ('data', sub)  # Return category and subcategory
    if top == 'models':  # If top-level is 'models'
        # Capture model subdirectories if present; otherwise mark as misc.
        sub = parts[1] if len(parts) > 1 else 'misc'  # Determine subcategory
        if sub in ('model_a', 'model_b', 'archive'):  # Specific model subcategories
            return ('models', sub)  # Return category and subcategory
        return ('models', 'misc')  # Default model subcategory
    if top == 'metrics':  # If top-level is 'metrics'
        # Categorize metrics subdirectories such as cv/ and holdout/.
        sub = parts[1] if len(parts) > 1 else 'misc'  # Determine subcategory
        return ('metrics', sub)  # Return category and subcategory
    if top == 'plots':  # If top-level is 'plots'
        # Group plots by their immediate subdirectory.
        sub = parts[1] if len(parts) > 1 else 'misc'  # Determine subcategory
        return ('plots', sub)  # Return category and subcategory
    if top == 'reports':  # If top-level is 'reports'
        # Reports/audits are separated from summary reports.
        if len(parts) > 1 and parts[1] == 'audits':  # Check for 'audits' subdirectory
            return ('reports', 'audits')  # Return category and subcategory
        return ('reports', 'summaries')  # Default reports subcategory
    if top == 'configs':  # If top-level is 'configs'
        # Config files are bucketed by filename conventions.
        fname = parts[-1]  # Get the filename
        if fname == 'latest.json':  # Specific config file
            return ('configs', 'latest')  # Return category and subcategory
        if fname.startswith('columns'):  # Config files starting with 'columns'
            return ('configs', 'columns')  # Return category and subcategory
        return ('configs', 'misc')  # Default config subcategory
    if top == 'scripts':  # If top-level is 'scripts'
        # All executable helper scripts are grouped under utilities.
        return ('scripts', 'utilities')  # Return category and subcategory

    # Default category when no other rule matches.
    return ('root', 'misc')  # Default category for unmatched paths


def load_run_id_from_summary(root: Path) -> str:  # Function to load run ID from project summary or manifest
    # Look for a summary pointer file that may reference a timestamped project summary.
    pointer = root / 'reports' / 'project_summary.md'  # Path to project summary pointer
    if pointer.exists():  # Check if pointer file exists
        try:
            # Read content defensively to tolerate encoding issues.
            txt = pointer.read_text(encoding='utf-8', errors='ignore')  # Read file content
            # Try to find project_summary_YYYYMMDD_HHMM.md in the text.
            import re  # Import regular expression module
            m = re.search(r'project_summary_(\d{8}_\d{4})\.md', txt)  # Search for pattern
            if m:  # If pattern found
                # Use the captured timestamp string as run_id.
                return m.group(1)  # Return captured timestamp
        except Exception:  # Catch any exceptions during processing
            # If anything goes wrong, fall through to other strategies.
            pass  # Ignore exception and continue
    # fallback: use previous manifest if present
    manifest = root / 'manifest.json'  # Path to manifest file
    if manifest.exists():  # Check if manifest file exists
        try:
            # Parse the existing manifest and reuse its run_id if available.
            data = json.loads(manifest.read_text(encoding='utf-8'))  # Load JSON from manifest
            if isinstance(data, dict) and 'run_id' in data:  # Check for 'run_id' in data
                return str(data['run_id'])  # Return existing run ID
        except Exception:  # Catch any exceptions during parsing
            # Ignore parse errors and continue to final fallback.
            pass  # Ignore exception and continue
    # ultimate fallback: current timestamp
    return datetime.utcnow().strftime('%Y%m%d_%H%M')  # Return current UTC timestamp as run ID


def main():  # Main function to regenerate the manifest
    # The repo root is two directories up from this script (scripts/ -> project root).
    root = Path(__file__).resolve().parent.parent  # Determine repository root path
    # Accumulate file metadata records here.
    files = []  # List to store file metadata

    for dirpath, dirnames, filenames in os.walk(root):  # Walk through directory tree
        # Skip directories not part of the repo manifest (e.g., .git if present).
        if '.git' in dirnames:  # Check for .git directory
            dirnames.remove('.git')  # Remove .git from directories to visit
        for fn in filenames:  # Iterate through files in current directory
            # Skip the manifest we are writing to avoid self-inclusion.
            if fn == 'manifest.json':  # Check if file is manifest.json
                continue  # Skip manifest file
            # Construct the full path to the file candidate.
            p = Path(dirpath) / fn  # Create full path to file
            # Only include regular files; exclude symlinks or special files.
            try:
                if not p.is_file():  # Check if it's a regular file
                    continue  # Skip if not a regular file
            except Exception:  # Catch exceptions during file check
                # If the check fails (e.g., permissions), skip the file.
                continue  # Skip file if check fails
            # Collect file size in bytes.
            size = p.stat().st_size  # Get file size
            # Compute SHA256 digest for integrity.
            digest = sha256_file(p)  # Compute SHA256 hash
            # Determine the file's category and subcategory for organization.
            category, subcategory = categorize(root, p)  # Categorize the file
            # Append a normalized metadata record to the list.
            files.append({
                'path': str(p.relative_to(root)).replace('\\', '/'),  # Relative path with forward slashes
                'size_bytes': int(size),  # File size
                'sha256': digest,  # SHA256 hash
                'category': category,  # File category
                'subcategory': subcategory,  # File subcategory
            })  # Add file metadata to list

    # Build the final manifest object with metadata and sorted file entries.
    out = {
        'run_id': load_run_id_from_summary(root),  # Get run ID
        'generated_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Generation timestamp
        'files': sorted(files, key=lambda x: x['path'])  # Sorted list of file metadata
    }  # Create manifest dictionary

    # Write the manifest to the repo root with pretty formatting.
    out_path = root / 'manifest.json'  # Path to output manifest file
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')  # Write JSON to file
    # Provide a console summary of how many files were indexed.
    print(f"Wrote manifest.json with {len(files)} files")  # Print summary message


if __name__ == '__main__':  # Script entry point
    # Execute the script entrypoint when run directly.
    main()  # Call the main function