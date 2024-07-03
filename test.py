import re

def check_text_pattern(text):
    pattern = r"^\d{4}[a-zA-Z]{3}$"
    if re.match(pattern, text):
        return True
    else:
        return False

# Example usage
text = "4467HXB"

print(check_text_pattern(text))  # Tru