import logging
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("OSINT_Tool")


def generate_stix_report(results: Dict[str, Any], output_file: str):
    """
    Generate STIX 2.1 format export (industry standard for threat intelligence).
    
    Args:
        results: Results dictionary
        output_file: Output file path
    """
    logger.info(f"Generating STIX 2.1 report: {output_file}")
    
    target = results.get('target', 'Unknown')
    target_type = results.get('target_type', 'Unknown')
    
    # STIX Bundle
    stix_bundle = {
        "type": "bundle",
        "id": f"bundle--{_generate_uuid()}",
        "spec_version": "2.1",
        "objects": []
    }
    
    # Create Identity object for target
    identity_obj = {
        "type": "identity",
        "id": f"identity--{_generate_uuid()}",
        "created": datetime.now().isoformat() + "Z",
        "modified": datetime.now().isoformat() + "Z",
        "name": target,
        "identity_class": "individual" if target_type == "individual" else "organization",
        "description": f"OSINT target: {target}"
    }
    stix_bundle["objects"].append(identity_obj)
    
    # Add social media profiles as Observed-Data
    for profile in results.get('social_media', []):
        observed_data = {
            "type": "observed-data",
            "id": f"observed-data--{_generate_uuid()}",
            "created": datetime.now().isoformat() + "Z",
            "modified": datetime.now().isoformat() + "Z",
            "first_observed": datetime.now().isoformat() + "Z",
            "last_observed": datetime.now().isoformat() + "Z",
            "number_observed": 1,
            "objects": {
                "0": {
                    "type": "url",
                    "value": profile.get('url', '')
                }
            },
            "labels": [
                "social-media",
                profile.get('platform', 'unknown').lower(),
                profile.get('status', 'unknown').lower()
            ]
        }
        stix_bundle["objects"].append(observed_data)
    
    # Add email addresses as Observed-Data
    if 'emails' in results and results['emails']:
        for email in results['emails'].get('emails_generated', []):
            observed_data = {
                "type": "observed-data",
                "id": f"observed-data--{_generate_uuid()}",
                "created": datetime.now().isoformat() + "Z",
                "modified": datetime.now().isoformat() + "Z",
                "first_observed": datetime.now().isoformat() + "Z",
                "last_observed": datetime.now().isoformat() + "Z",
                "number_observed": 1,
                "objects": {
                    "0": {
                        "type": "email-addr",
                        "value": email
                    }
                },
                "labels": ["email-enumeration"]
            }
            stix_bundle["objects"].append(observed_data)
    
    # Add search results as Observed-Data
    for result in results.get('search_engines', []):
        observed_data = {
            "type": "observed-data",
            "id": f"observed-data--{_generate_uuid()}",
            "created": datetime.now().isoformat() + "Z",
            "modified": datetime.now().isoformat() + "Z",
            "first_observed": datetime.now().isoformat() + "Z",
            "last_observed": datetime.now().isoformat() + "Z",
            "number_observed": 1,
            "objects": {
                "0": {
                    "type": "url",
                    "value": result.get('url', '')
                }
            },
            "labels": [
                "search-result",
                result.get('source', 'unknown').lower()
            ]
        }
        stix_bundle["objects"].append(observed_data)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stix_bundle, f, indent=2)
    
    logger.info(f"✓ STIX 2.1 report saved to {output_file} ({len(stix_bundle['objects'])} objects)")


def _generate_uuid() -> str:
    """Generate a simple UUID for STIX objects."""
    import uuid
    return str(uuid.uuid4())
