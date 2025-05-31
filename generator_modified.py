"""
Program: generator.py
Author: Ken
Generates and displays sentences using a simple grammar
and vocabulary. Words are chosen at random.
"""

import random

def getWords(filename):
    """Reads words from a file and returns them as a tuple."""
    try:
        with open(filename, 'r') as file:
            word_list = [line.strip().upper() for line in file if line.strip()]
        return tuple(word_list)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return ()

# Load vocabulary from files
articles = getWords("/home/vboxuser/Downloads/PostLab/articles.txt")
nouns = getWords("/home/vboxuser/Downloads/PostLab/nouns.txt")
verbs = getWords("/home/vboxuser/Downloads/PostLab/verbs.txt")
prepositions = getWords("/home/vboxuser/Downloads/PostLab/prepositions.txt")

def sentence():
    """Builds and returns a sentence."""
    return nounPhrase() + " " + verbPhrase()

def nounPhrase():
    """Builds and returns a noun phrase."""
    return random.choice(articles) + " " + random.choice(nouns)

def verbPhrase():
    """Builds and returns a verb phrase."""
    return random.choice(verbs) + " " + nounPhrase() + " " + prepositionalPhrase()

def prepositionalPhrase():
    """Builds and returns a prepositional phrase."""
    return random.choice(prepositions) + " " + nounPhrase()

def main():
    """Allows the user to input the number of sentences to generate."""
    try:
        number = int(input("Enter the number of sentences: "))
        for count in range(number):
            print(sentence())
    except ValueError:
        print("Invalid input. Please enter an integer.")

# The entry point for program execution
if __name__ == "__main__":
    main()
