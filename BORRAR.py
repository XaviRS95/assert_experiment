import re

text = """
bdfmmgenfgplkgbabkgjpdapegcijbll: assert( (a == 4'b0001) ? (y == 2'b01) : 1 )  else $error("Error in immediate assert bdfmmgenfgplkgbabkgjpdapegcijbll");
okncjhbdipnlkcmipcbhkkkioonhhddi: assert( (a == 4'b0010) ? (y == 2'b10) : 1 )  else $error("Error in immediate assert okncjhbdipnlkcmipcbhkkkioonhhddi");
bcamklfafioakgcnpeadkaaceokebgai: assert( (a == 4'b0011) ? (y == 2'b11) : 1 )  else $error("Error in immediate assert bcamklfafioakgcnpeadkaaceokebgai");
"""

# Regex breakdown:
# (assert\(.*?\)) -> Matches 'assert(', then any character (non-greedy), then ')'
# \s+else         -> Matches the space and the word 'else' to ensure we stop at the right spot
pattern = r"(assert\(.*?\))\s+else"

matches = re.findall(pattern, text)

for match in matches:
    print(match)