# See http://a-coda.tumblr.com/post/85425656701/starting-from-zero
# Adapted from https://github.com/dhconnelly/paip-python/blob/master/paip/eliza.py
 
import random
import string
import zmq
 
def service (ctx, address, rules, default_responses):
    s = ctx.socket( zmq.REP )
    s.bind( address )
    while True:
        try:
            input = s.recv()
            if not input:
                continue
        except:
            break
        response = respond(rules, input, default_responses)
        s.send( response )
 
def interact (ctx, address, prompt):
    s = ctx.socket( zmq.REQ )
    s.connect( address )
    while True:
        try:
            input = remove_punct(raw_input(prompt).upper())
            if not input:
                continue
        except:
            break
        s.send( input )
        print s.recv()
 
def respond(rules, input, default_responses):
    input = input.split() # match_pattern expects a list of tokens
    matching_rules = []
    for pattern, transforms in rules:
        pattern = pattern.split()
        replacements = match_pattern(pattern, input)
        if replacements:
            matching_rules.append((transforms, replacements))
    if matching_rules:
        responses, replacements = random.choice(matching_rules)
        response = random.choice(responses)
    else:
        replacements = {}
        response = random.choice(default_responses)
    for variable, replacement in replacements.items():
        replacement = ' '.join(switch_viewpoint(replacement))
        if replacement:
            response = response.replace('?' + variable, replacement)
    
    return response
 
def match_pattern(pattern, input, bindings=None):
    if bindings is False:
        return False
    if pattern == input:
        return bindings
    bindings = bindings or {}
    if is_segment(pattern):
        token = pattern[0] # segment variable is the first token
        var = token[2:] # segment variable is of the form ?*x
        return match_segment(var, pattern[1:], input, bindings)
    elif is_variable(pattern):
        var = pattern[1:] # single variables are of the form ?foo
        return match_variable(var, [input], bindings)
    elif contains_tokens(pattern) and contains_tokens(input):
        return match_pattern(pattern[1:],
                             input[1:],
                             match_pattern(pattern[0], input[0], bindings))
    else:
        return False
 
def match_segment(var, pattern, input, bindings, start=0):
    if not pattern:
        return match_variable(var, input, bindings)
    word = pattern[0]
    try:
        pos = start + input[start:].index(word)
    except ValueError:
        return False
    var_match = match_variable(var, input[:pos], dict(bindings))
    match = match_pattern(pattern, input[pos:], var_match)
    if not match:
        return match_segment(var, pattern, input, bindings, start + 1)
    return match
 
def match_variable(var, replacement, bindings):
    binding = bindings.get(var)
    if not binding:
        bindings.update({var: replacement})
        return bindings
    if replacement == bindings[var]:
        return bindings
    return False
 
def contains_tokens(pattern):
    return type(pattern) is list and len(pattern) > 0
 
def is_variable(pattern):
    return (type(pattern) is str
            and pattern[0] == '?'
            and len(pattern) > 1
            and pattern[1] != '*'
            and pattern[1] in string.letters
            and ' ' not in pattern)
 
def is_segment(pattern):
    return (type(pattern) is list
            and pattern
            and len(pattern[0]) > 2
            and pattern[0][0] == '?'
            and pattern[0][1] == '*'
            and pattern[0][2] in string.letters
            and ' ' not in pattern[0])
 
def replace(word, replacements):
    for old, new in replacements:
        if word == old:
            return new
    return word
 
def switch_viewpoint(words):
    replacements = [('I', 'YOU'),
                    ('YOU', 'I'),
                    ('ME', 'YOU'),
                    ('MY', 'YOUR'),
                    ('AM', 'ARE'),
                    ('ARE', 'AM')]
    return [replace(word, replacements) for word in words]
 
def remove_punct(string):
    if string.endswith('?'):
        string = string[:-1]
    return (string.replace(',', '')
            .replace('.', '')
            .replace(';', '')
            .replace('!', ''))
 
import json
import sys
 
rules = {
    "?*x hello ?*y": [
        "How do you do. Please state your problem."
        ],
    "?*x computer ?*y": [
        "Do computers worry you?",
        "What do you think about machines?",
        "Why do you mention computers?",
        "What do you think machines have to do with your problem?",
        ],
    "?*x name ?*y": [
        "I am not interested in names",
        ],
    "?*x sorry ?*y": [
        "Please don't apologize",
        "Apologies are not necessary",
        "What feelings do you have when you apologize",
        ],
    "?*x I remember ?*y": [
        "Do you often think of ?y?",
        "Does thinking of ?y bring anything else to mind?",
        "What else do you remember?",
        "Why do you recall ?y right now?",
        "What in the present situation reminds you of ?y?",
        "What is the connection between me and ?y?",
        ],
    "?*x do you remember ?*y": [
        "Did you think I would forget ?y?",
        "Why do you think I should recall ?y now?",
        "What about ?y?",
        "You mentioned ?y",
        ],
    "?*x I want ?*y": [
        "What would it mean if you got ?y?",
        "Why do you want ?y?",
        "Suppose you got ?y soon."
        ],
    "?*x if ?*y": [
        "Do you really think it's likely that ?y?",
        "Do you wish that ?y?",
        "What do you think about ?y?",
        "Really--if ?y?"
        ],
    "?*x I dreamt ?*y": [
        "How do you feel about ?y in reality?",
        ],
    "?*x dream ?*y": [
        "What does this dream suggest to you?",
        "Do you dream often?",
        "What persons appear in your dreams?",
        "Don't you believe that dream has to do with your problem?",
        ],
    "?*x my mother ?*y": [
        "Who else in your family ?y?",
        "Tell me more about your family",
        ],
    "?*x my father ?*y": [
        "Your father?",
        "Does he influence you strongly?",
        "What else comes to mind when you think of your father?",
        ],
    "?*x I am glad ?*y": [
        "How have I helped you to be ?y?",
        "What makes you happy just now?",
        "Can you explain why you are suddenly ?y?",
        ],
    "?*x I am sad ?*y": [
        "I am sorry to hear you are depressed",
        "I'm sure it's not pleasant to be sad",
        ],
    "?*x are like ?*y": [
        "What resemblence do you see between ?x and ?y?",
        ],
    "?*x is like ?*y": [
        "In what way is it that ?x is like ?y?",
        "What resemblence do you see?",
        "Could there really be some connection?",
        "How?",
        ],
    "?*x alike ?*y": [
        "In what way?",
        "What similarities are there?",
        ],
    "?* same ?*y": [
        "What other connections do you see?",
        ],
    "?*x no ?*y": [
        "Why not?",
        "You are being a bit negative.",
        "Are you saying 'No' just to be negative?"
        ],
    "?*x I was ?*y": [
        "Were you really?",
        "Perhaps I already knew you were ?y.",
        "Why do you tell me you were ?y now?"
        ],
    "?*x was I ?*y": [
        "What if you were ?y?",
        "Do you think you were ?y?",
        "What would it mean if you were ?y?",
        ],
    "?*x I am ?*y": [
        "In what way are you ?y?",
        "Do you want to be ?y?",
        ],
    "?*x am I ?*y": [
        "Do you believe you are ?y?",
        "Would you want to be ?y?",
        "You wish I would tell you you are ?y?",
        "What would it mean if you were ?y?",
        ],
    "?*x am ?*y": [
        "Why do you say 'AM?'",
        "I don't understand that"
        ],
    "?*x are you ?*y": [
        "Why are you interested in whether I am ?y or not?",
        "Would you prefer if I weren't ?y?",
        "Perhaps I am ?y in your fantasies",
        ],
    "?*x you are ?*y": [
        "What makes you think I am ?y?",
        ],
    "?*x because ?*y": [
        "Is that the real reason?",
        "What other reasons might there be?",
        "Does that reason seem to explain anything else?",
        ],
    "?*x were you ?*y": [
        "Perhaps I was ?y?",
        "What do you think?",
        "What if I had been ?y?",
        ],
    "?*x I can't ?*y": [
        "Maybe you could ?y now",
        "What if you could ?y?",
        ],
    "?*x I feel ?*y": [
        "Do you often feel ?y?"
        ],
    "?*x I felt ?*y": [
        "What other feelings do you have?"
        ],
    "?*x I ?*y you ?*z": [
        "Perhaps in your fantasy we ?y each other",
        ],
    "?*x why don't you ?*y": [
        "Should you ?y yourself?",
        "Do you believe I don't ?y?",
        "Perhaps I will ?y in good time",
        ],
    "?*x yes ?*y": [
        "You seem quite positive",
        "You are sure?",
        "I understand",
        ],
    "?*x someone ?*y": [
        "Can you be more specific?",
        ],
    "?*x everyone ?*y": [
        "Surely not everyone",
        "Can you think of anyone in particular?",
        "Who, for example?",
        "You are thinking of a special person",
        ],
    "?*x always ?*y": [
        "Can you think of a specific example?",
        "When?",
        "What incident are you thinking of?",
        "Really--always?",
        ],
    "?*x what ?*y": [
        "Why do you ask?",
        "Does that question interest you?",
        "What is it you really want to know?",
        "What do you think?",
        "What comes to your mind when you ask that?",
        ],
    "?*x perhaps ?*y": [
        "You do not seem quite certain",
        ],
    "?*x are ?*y": [
        "Did you think they might not be ?y?",
        "Possibly they are ?y",
        ],
    }
 
default_responses = [
    "Very interesting",
    "I am not sure I understand you fully",
    "What does that suggest to you?",
    "Please continue",
    "Go on",
    "Do you feel strongly about discussing such things?",
    ]
 
def make_rules_list ():
    rules_list = []
    for pattern, transforms in rules.items():
        pattern = remove_punct(str(pattern.upper())) # kill unicode
        transforms = [str(t).upper() for t in transforms]
        rules_list.append((pattern, transforms))
    return rules_list
 
def main():
    ctx = zmq.Context.instance()
    address = "tcp://127.0.0.1:5555"
    if len(sys.argv) > 1 and sys.argv[1] == "service":
        service( ctx, address, make_rules_list(), map(str.upper, default_responses) )
    else:
        interact( ctx, address, 'ELIZA> ' )
 
if __name__ == '__main__':
    main()
