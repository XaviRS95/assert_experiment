import re, uuid

def clean_whitespace(raw_text:str) -> str:
    """
    Standardizes formatting by collapsing vertical and horizontal whitespace.
    Useful for turning jagged port/parameter lists into a clean, readable format.
    """
    if raw_text:
        clean_lines = []
        for line in raw_text.splitlines():
            # 1. Strip leading/trailing whitespace from the line
            line = line.strip()

            # 2. Replace 2 or more whitespace characters (\s{2,}) with a single space
            # This preserves the single space between 'input' and 'logic'
            line = re.sub(r'\s{2,}', ' ', line)

            if line:  # Only add if the line isn't empty
                clean_lines.append(line)

        return "\n".join(clean_lines)
    else:
        return ''

def commentless_code(code: str) -> str:
    """
    Removes both single-line (//) and multi-line (/* */) comments.
    Also cleans up leftover empty lines to prevent 'swiss cheese' code formatting.
    """
    pattern = r'(\/\*[\s\S]*?\*\/|\/\/.*)'
    clean_code = code
    for match in re.finditer(pattern, code):
        clean_code = clean_code.replace(match.group(0), '')
    clean_code = re.sub(r'(?m)^[ \t]*\n', '', clean_code)
    return clean_code

def contains_assertions(code):
    """Check if code contains actual assertions"""

    # Clean and extract from markdown
    if not code:
        return False

    # Parse for assertion constructs
    patterns = [
        r'assert\s*\(',  # Immediate assertions
        r'assert\s+property\s*\(',  # Concurrent assertions
        r'cover\s+property\s*\(',  # Cover properties
        r'assume\s+property\s*\(',  # Assume properties
        r'ap_\w+\s*:\s*assert\s+property',  # Labeled assertions
    ]

    for pattern in patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return True

    # Check for SVA sequences/temporal logic
    sv_keywords = ['|=>', '|->', '##', '[*', '[=', 'throughout']
    for keyword in sv_keywords:
        if keyword in code:
            return True

    return False

def get_alpha_uuid():
    # Generate a standard UUID4
    raw_uuid = uuid.uuid4().hex

    # Create a mapping table: 0-9 -> g-p
    # This ensures no overlap with the existing a-f letters
    mapping = str.maketrans("0123456789", "ghijklmnop")

    return raw_uuid.translate(mapping)