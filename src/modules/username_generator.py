import logging
from typing import List, Set

logger = logging.getLogger("OSINT_Tool")


class UsernameGenerator:
    """
    Generates username variations for comprehensive social media searches.
    Creates common patterns, leet speak variations, and separator combinations.
    """
    
    def __init__(self):
        self.leet_map = {
            'a': ['a', '4', '@'],
            'e': ['e', '3'],
            'i': ['i', '1', '!'],
            'o': ['o', '0'],
            's': ['s', '5', '$'],
            't': ['t', '7'],
            'l': ['l', '1'],
            'g': ['g', '9'],
            'b': ['b', '8']
        }
        
        self.separators = ['', '.', '_', '-']
        self.common_suffixes = ['', '1', '123', '2023', '2024', '01']
    
    def generate_basic_variations(self, first_name: str, last_name: str = None) -> Set[str]:
        """
        Generate basic username variations without leet speak.
        
        Args:
            first_name: First name
            last_name: Last name (optional)
            
        Returns:
            Set of username variations
        """
        variations = set()
        first = first_name.lower().strip()
        
        if not last_name:
            # Single name variations
            variations.add(first)
            if len(first) > 1:
                variations.add(first[0])  # First initial
            return variations
        
        last = last_name.lower().strip()
        f_initial = first[0] if first else ''
        l_initial = last[0] if last else ''
        
        # Common patterns
        for sep in self.separators:
            # firstname.lastname
            variations.add(f"{first}{sep}{last}")
            # lastname.firstname
            variations.add(f"{last}{sep}{first}")
            # f.lastname
            variations.add(f"{f_initial}{sep}{last}")
            # firstname.l
            variations.add(f"{first}{sep}{l_initial}")
            # fl (initials)
            if sep == '':
                variations.add(f"{f_initial}{l_initial}")
        
        # Just first or last name
        variations.add(first)
        variations.add(last)
        
        return variations
    
    def apply_leet_speak(self, username: str, depth: int = 1) -> Set[str]:
        """
        Apply leet speak transformations to a username.
        
        Args:
            username: Base username
            depth: How many characters to transform (1-3)
            
        Returns:
            Set of leet speak variations
        """
        if depth < 1:
            return {username}
        
        variations = {username}
        
        # Apply simple leet speak (depth 1)
        for char, replacements in self.leet_map.items():
            if char in username:
                for replacement in replacements[1:]:  # Skip the original character
                    variations.add(username.replace(char, replacement, 1))
        
        # For depth > 1, apply multiple transformations
        if depth > 1:
            temp_variations = set(variations)
            for var in temp_variations:
                # Apply one more transformation
                for char, replacements in self.leet_map.items():
                    if char in var:
                        for replacement in replacements[1:]:
                            variations.add(var.replace(char, replacement, 1))
        
        return variations
    
    def add_suffixes(self, username: str) -> Set[str]:
        """
        Add common number suffixes to username.
        
        Args:
            username: Base username
            
        Returns:
            Set of username + suffix combinations
        """
        variations = set()
        for suffix in self.common_suffixes:
            variations.add(f"{username}{suffix}")
        return variations
    
    def generate_all_variations(
        self,
        first_name: str,
        last_name: str = None,
        include_leet: bool = True,
        include_suffixes: bool = False,
        max_variations: int = 50
    ) -> List[str]:
        """
        Generate all username variations with optional leet speak and suffixes.
        
        Args:
            first_name: First name
            last_name: Last name (optional)
            include_leet: Include leet speak variations
            include_suffixes: Include number suffixes
            max_variations: Maximum number of variations to return
            
        Returns:
            List of username variations
        """
        logger.info(f"Generating username variations for: {first_name} {last_name or ''}")
        
        # Start with basic variations
        variations = self.generate_basic_variations(first_name, last_name)
        
        # Add leet speak variations
        if include_leet:
            leet_variations = set()
            for var in list(variations)[:20]:  # Limit to avoid explosion
                leet_variations.update(self.apply_leet_speak(var, depth=1))
            variations.update(leet_variations)
        
        # Add suffixes
        if include_suffixes:
            suffix_variations = set()
            for var in list(variations)[:20]:  # Limit to avoid explosion
                suffix_variations.update(self.add_suffixes(var))
            variations.update(suffix_variations)
        
        # Remove empty strings and very short usernames
        variations = {v for v in variations if len(v) >= 2}
        
        # Sort by length (shorter first, more common)
        sorted_variations = sorted(variations, key=lambda x: (len(x), x))
        
        # Limit to max_variations
        result = sorted_variations[:max_variations]
        
        logger.info(f"Generated {len(result)} username variations")
        return result
    
    def generate_from_full_name(
        self,
        full_name: str,
        include_leet: bool = False,
        include_suffixes: bool = False,
        max_variations: int = 30
    ) -> List[str]:
        """
        Generate variations from a full name string.
        
        Args:
            full_name: Full name (will be split)
            include_leet: Include leet speak variations
            include_suffixes: Include number suffixes
            max_variations: Maximum variations to return
            
        Returns:
            List of username variations
        """
        parts = full_name.strip().split()
        
        if not parts:
            return []
        
        first_name = parts[0]
        last_name = ' '.join(parts[1:]) if len(parts) > 1 else None
        
        return self.generate_all_variations(
            first_name=first_name,
            last_name=last_name,
            include_leet=include_leet,
            include_suffixes=include_suffixes,
            max_variations=max_variations
        )


def generate_username_variations(
    target_name: str,
    include_leet: bool = False,
    include_suffixes: bool = False,
    max_variations: int = 30
) -> List[str]:
    """
    Convenience function to generate username variations.
    
    Args:
        target_name: Full name of target
        include_leet: Include leet speak variations
        include_suffixes: Include number suffixes
        max_variations: Maximum variations to return
        
    Returns:
        List of username variations
    """
    generator = UsernameGenerator()
    return generator.generate_from_full_name(
        full_name=target_name,
        include_leet=include_leet,
        include_suffixes=include_suffixes,
        max_variations=max_variations
    )
