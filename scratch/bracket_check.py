import sys

def check_brackets(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    lines = content.splitlines()
    
    for line_idx, line in enumerate(lines, 1):
        # simple check, skip comments
        if line.strip().startswith('//') or line.strip().startswith('/*'):
            continue
        
        in_string = False
        string_char = None
        escape = False
        
        for char_idx, char in enumerate(line, 1):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif string_char == char:
                    in_string = False
                continue
            
            if in_string:
                continue
                
            if char in mapping.values():
                stack.append((char, line_idx, char_idx))
            elif char in mapping.keys():
                if not stack:
                    print(f"Mismatched closing bracket '{char}' at line {line_idx}, col {char_idx}")
                    return False
                top_char, top_line, top_col = stack.pop()
                if top_char != mapping[char]:
                    print(f"Mismatched bracket: '{char}' at line {line_idx}, col {char_idx} doesn't match '{top_char}' from line {top_line}, col {top_col}")
                    return False
                    
    if stack:
        print(f"Unclosed brackets remain: {stack}")
        return False
        
    print("All brackets match perfectly!")
    return True

if __name__ == '__main__':
    check_brackets('static/js/app.js')
