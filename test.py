import re
import difflib

def compare_texts(old_text, new_text):
    # Split the texts into sentences
    old_sentences = re.split(r'(?<=[.!?])\s+', old_text)
    new_sentences = re.split(r'(?<=[.!?])\s+', new_text)
    
    # Compare the sentences using difflib
    differ = difflib.Differ()
    diff = list(differ.compare(old_sentences, new_sentences))
    
    # Get the missing and new sentences
    missing_sentences = []
    new_sentences = []
    for sentence in diff:
        if sentence.startswith('- '):
            missing_sentences.append(sentence[2:])
        elif sentence.startswith('+ '):
            new_sentences.append(sentence[2:])
    
    return missing_sentences, new_sentences
old_text = "It is 50% sale! This is awesome! For some time now I have been searching for this. Please call 123-457 for more info."
new_text = "It is 20% sale! This is amazing and awesome! For some time now I have been searching for this. Please call 123-456 for more info."

missing_sentences, new_sentences = compare_texts(old_text, new_text)

print("Missing sentences:", missing_sentences)
print("New sentences:", new_sentences)
